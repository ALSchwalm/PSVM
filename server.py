#!/usr/bin/env python

from wsgiref.simple_server import make_server
from cgi import parse_qs, escape
from mimetypes import guess_type
from hashlib import sha512
from Cookie import SimpleCookie
from collections import defaultdict

from markup import parse_markup
from settings import *
from database import *
from mail import *

#Go ahead and open the templates, we're bound to need them
frame = open("templates/frame.html").read()

templates = {#open page templates
             "404" : frame.format(content=open("templates/404.html").read()),
             "index" : frame.format(content=open("templates/index.html").read()),
             "login" : frame.format(content=open("templates/login.html").read()),
             "register" : frame.format(content=open("templates/register.html").read()),
             
             #open non-page templates - i.e. those not wrapped in the frame
             "login_link" : open("templates/login_link.html").read(),
             "logout_link" : open("templates/logout_link.html").read(),
             "post" : open("templates/post.html").read()}
 
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

def add_post(user_id, post):
   database.execute("INSERT INTO comments VALUES(NULL, ?, ?)", (user_id[0], post))

def compose_posts():
   posts = database.execute("SELECT users.username, comments.body FROM users, comments WHERE comments.user_id = users.user_id").fetchall()
   return "".join([templates["post"].format(username=post['username'],
                                            content=post['body']) for post in posts])

def handle_POST(environ, options):
   action = environ["PATH_INFO"]
   if action == "/new_post":
      user = is_login(environ)
      if user:
         new_post = options.get("new_post", [""])[0]

         # Always escape user input to avoid script injection
         #TODO store the unmodified version to allow edits
         new_post = parse_markup(escape(new_post))

         add_post(user, new_post)
         return [('Location', URL + "/index.html")]
      else:
         return [('Location', URL + "/login.html?prompt=restricted")]

   #TODO redirect to success or failure
   elif action == "/login":
      username = options.get("username", [""])[0]
      password = options.get("password", [""])[0]
      
      if username and (username[0] in ('"', "'") or password[0] in ('"', "'")):
        return [('Location', "http://www.youtube.com/embed/rhr44HD49-U?autoplay=1&loop=1&playlist=rhr44HD49-U&showinfo=0")]
      
      q = database.execute("SELECT user_id, pass_hash, verified FROM users WHERE username = ? AND pass_hash = ?", (username, sha512(password).hexdigest()))
      result = q.fetchone()
      
      if not result or not username or not password:
        return [('Location', URL + "/login.html?prompt=failed")]
      elif result["verified"] != True:
        return [('Location', URL + "/login.html?prompt=unverified")]
        
      return [('Location', URL + "/index.html"),
              ("Set-Cookie", "USERID="+str(result["user_id"])),
              ("Set-Cookie", "PASSHASH="+str(result["pass_hash"]))]

   elif action == "/logout":
      return [('Location', URL + "/index.html"),
              ("Set-Cookie", "USERID=; Expires=Thu, 01-Jan-1970 00:00:10 GMT;"),
              ("Set-Cookie", "PASSHASH=; Expires=Thu, 01-Jan-1970 00:00:10 GMT;")]
      
   elif action == "/register":
      username = options.get("username", [""])[0]
      password = options.get("password", [""])[0]
      password_verify = options.get("password", ["", ""])[1]
      email = options.get("email", [""])[0]
      
      if password != password_verify:
         return [('Location', URL + "/register.html?prompt=mismatch")]
      elif not username or not password or not email:
         return [('Location', URL + "/register.html?prompt=blank")]
      elif len(username) < 5 or len(password) < 6:
         return [('Location', URL + "/register.html?prompt=length")]
      elif not validate_email(email):
         return [('Location', URL + "/register.html?prompt=email")]
      else:
         q = database.execute("SELECT user_id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
         if q:
            return [('Location', URL + "/register.html?prompt=duplicate")]
         else:
            database.execute("INSERT INTO users VALUES (NULL, ?, ?, ?, 0)", (username, sha512(password).hexdigest(), email))
            
            #FIXME This is possibly incorrect the "lastrowid" may not be the user_id
            send_confirmation(username, database.lastrowid, email)
            
            #TODO check that this acutally worked
            #TODO add javascript to redirect to login if successful
            return [('Location', URL + "/register.html?prompt=success")]
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
                                       login_link=templates["login_link"] if not is_login(environ) 
                                       else templates["logout_link"].format(username=is_login(environ)[1]))
      
   elif page_name == "/login.html":
      prompts = defaultdict(str, { 
        "restricted" : "You must login to complete this action</br>",
        "unverified" : "You must verify your account before you can login</br>",
        "verified" : "You have successfully verified your account. Please login</br>",
        "failed" : "Invalid username or password</br>"
      })
   
      page = templates["login"].format(prompt=prompts[qs.get("prompt", [None])[0]])

   elif page_name == "/register.html":
      prompts = defaultdict(str, { 
         "success" : "Registration successful</br>",
         "blank" : "Username, password, and email must be non-empty</br>",
         "mismatch" : "Password and verification must match</br>",
         "duplicate" : "A user with that name or email is already registered</br>",
         "length" : "Username must be more than 5 characters, password must be more than 6</br>",
         "email" : "Invalid email address"
      })
      
      page = templates["register"].format(prompt=prompts[qs.get("prompt", [None])[0]])
   
   elif page_name.split("/")[1] == "verify":
      if page_name in live_links:
         print live_links[page_name]
         database.execute("UPDATE users SET verified = 1 WHERE user_id = ?", (live_links[page_name],))
         del live_links[page_name]
         return [('Location', URL + "/login.html?prompt=verified")], "301 REDIRECT", "" 
      else:
         return [('Location', URL + "/login.html")], "301 REDIRECT", "" 
            
   #Try to open anything else. Useful for javascript etc.
   #TODO this is (very) possibly unsafe
   elif page_name.split(".")[-1] in ("js", "html", "css", "png", "jpg", "gif"):
      page = open(page_name[1:]).read()
      
   else:
      raise IOError

   status = '200 OK'
      
   #Determine MIME type
   mime = guess_type(page_name)[0] or "text/html" #default to text/html
      
   response_headers = [('Content-Type', mime),
                       ('Content-Length', str(len(page)))]
      
   return response_headers, status, page

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
      response_headers, status, response_body = compose_page(environ)

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
