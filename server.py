#!/usr/bin/env python

from wsgiref.simple_server import make_server
from cgi import parse_qs, escape
from mimetypes import guess_type
from urlparse import urlparse
from hashlib import sha512
from Cookie import SimpleCookie
from collections import defaultdict
import sqlite3


conn = sqlite3.connect('example.db')
conn.row_factory = sqlite3.Row
database = conn.cursor()

#Go ahead and open the templates, we're bound to need them
templates = {"404" : open("templates/404.html").read(),
             "index" : open("index.html").read(),
             "post" : open("templates/post.html").read(),
             "login" : open("templates/login.html").read(),
             "login_link" : open("templates/login_link.html").read(),
             "nice_try" : open("templates/nice_try.html").read()}

#To fix slow load times on windows with localhost see http://stackoverflow.com/a/1813778
URL = "http://localhost:8051"
parsed_MAIN_URL = urlparse(URL)
 
def is_login(environ):
   try:
      c = SimpleCookie(environ.get("HTTP_COOKIE",""))
      user_id = c["USERID"].value
      password_hash = c["PASSHASH"].value

      user = database.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
      
      if not user or user['pass_hash'] != password_hash:
         return False
  
      return (user_id, user["username"])

   except KeyError:
      return False

  
#This will be in the database
posts = []

#these methods will hit the database 
def add_post(post):
   global posts
   posts.append(post)

def compose_posts():
   global posts
   post_template = templates["post"]
   return "".join([post_template.format(content=body) for body in posts])

def handle_POST(environ, options):
   action = environ["PATH_INFO"]
   if action == "/new_post":
      if is_login(environ):
         new_post = options.get("new_post", [""])[0]

         # Always escape user input to avoid script injection
         new_post = escape(new_post)

         add_post(new_post)
         return [('Location', URL + "/index.html")]
      else:
         return [('Location', URL + "/login.html?prompt=restricted")]

   #TODO redirect to success or failure
   elif action == "/login":
      username = options.get("username", [""])[0]
      password = options.get("password", [""])[0]
      
      if username[0] in ('"', "'") or password[0] in ('"', "'"):
        return [('Location', URL + "/nice_try.html")]
      
      q = database.execute("SELECT user_id, pass_hash FROM users WHERE username = ? AND pass_hash = ?", (username, sha512(password).hexdigest()))
      result = q.fetchone()
      
      if not result or not username or not password:
        return [('Location', URL + "/login.html?prompt=failed")]
        
      #TODO get this from database
      return [('Location', URL + "/index.html"),
              ("Set-Cookie", "USERID="+str(result["user_id"])),
              ("Set-Cookie", "PASSHASH="+str(result["pass_hash"]))]
      
   else:
      return [('Location', URL + action)]
   
#bulk of the work ocurrs here
def compose_page(environ):
   page = ""
   page_name = environ["PATH_INFO"]
   qs = parse_qs(environ["QUERY_STRING"])
   
   #Compose any known page
   if page_name == "/index.html" or page_name == "/" or page_name == "":
      page = templates["index"].format(posts = compose_posts() or 'None',
                                       login_link=templates["login_link"] if not is_login(environ) else is_login(environ)[1])
      

   elif page_name == "/login.html":
      prompts = defaultdict(str, { 
        "restricted" : "You must login to complete this action</br>",
        "failed" : "Invalid username or password</br>"
      })
   
      page = templates["login"].format(prompt=prompts[qs.get("prompt", [None])[0]])

   elif page_name == "/nice_try.html":
     page = templates["nice_try"]
     
   #Try to open anything else. Useful for javascript etc.
   #TODO this is (very) possibly unsafe
   else:
      page = open(page_name[1:]).read()

   return page

def application(environ, start_response):
   # the environment variable CONTENT_LENGTH may be empty or missing
   try:
      request_body_size = int(environ.get('CONTENT_LENGTH', 0))
   except ValueError:
      request_body_size = 0 

   path = environ["PATH_INFO"]

   #Different handling for POST/GET. POSTS may require redirection etc.
   if environ["REQUEST_METHOD"] == "POST":
      request_body = environ['wsgi.input'].read(request_body_size)
      d = parse_qs(request_body)
      post_header  = handle_POST(environ,  d)

   try:
      response_body = compose_page(environ)
      status = '200 OK'
      
      #Determine MIME type
      mime = guess_type(path)[0] or "text/html" #default to text/html
      
      response_headers = [('Content-Type', mime),
                          ('Content-Length', str(len(response_body)))]

   except IOError:
      response_body = templates["404"]
      status = '404 NOT FOUND'
      response_headers = [('Content-Type', 'text/html'),
                          ('Content-Length', str(len(response_body)))]

   #Impliment PRG to prevent form resubmission
   if path == "/":
      start_response('301 REDIRECT', [('Location', URL + "/index.html")])
   elif environ["REQUEST_METHOD"] == "POST":
      start_response('301 REDIRECT', post_header)
   else:
      start_response(status, response_headers)

   return [response_body]

httpd = make_server(parsed_MAIN_URL.hostname, parsed_MAIN_URL.port, application)
httpd.serve_forever()
