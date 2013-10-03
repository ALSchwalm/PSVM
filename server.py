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
             "forgot" : frame.format(content=open("templates/forgot.html").read()),
             "reset" : frame.format(content=open("templates/reset_password.html").read()),
             
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


def default_header(page_name, page):
    status = '200 OK'
      
    #Determine MIME type
    mime = guess_type(page_name)[0] or "text/html" #default to text/html
      
    response_headers = [('Content-Type', mime),
                       ('Content-Length', str(len(page)))]
    return status, response_headers
    
def redirect_header(address):
    return '301 REDIRECT', [('Location', URL + address)]
      
                                            
def new_post(environ, start_response):
    request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    request_body = environ['wsgi.input'].read(request_body_size)
    options = parse_qs(request_body)
    user = is_login(environ)
    if user:
        new_post = options.get("new_post", [""])[0]

        # Always escape user input to avoid script injection
        #TODO store the unmodified version to allow edits
        new_post = parse_markup(escape(new_post))

        add_post(user, new_post)
        start_response(*redirect_header("/index.html"))
    else:
        start_response(*redirect_header("/login.html?prompt=restricted"))

def login_post(environ, start_response):
      request_body_size = int(environ.get('CONTENT_LENGTH', 0))
      request_body = environ['wsgi.input'].read(request_body_size)
      options = parse_qs(request_body)
      
      username = options.get("username", [""])[0]
      password = options.get("password", [""])[0]
      
      if username and (username[0] in ('"', "'") or password[0] in ('"', "'")):
        start_response(*redirect_header("http://www.youtube.com/embed/rhr44HD49-U?autoplay=1&loop=1&playlist=rhr44HD49-U&showinfo=0"))
      
      q = database.execute("SELECT user_id, pass_hash, verified FROM users WHERE username = ? AND pass_hash = ?", (username, sha512(password).hexdigest()))
      result = q.fetchone()
      
      if not result or not username or not password:
        start_response(*redirect_header("/login.html?prompt=failed"))
      elif result["verified"] != True:
        start_response(*redirect_header("/login.html?prompt=unverified"))
      else:
        start_response("301 REDIRECT", [('Location', URL + "/index.html"),
              ("Set-Cookie", "USERID="+str(result["user_id"])),
              ("Set-Cookie", "PASSHASH="+str(result["pass_hash"]))])

def logout(environ, start_response):
    start_response("301 REDIRECT", [('Location', URL + "/index.html"),
              ("Set-Cookie", "USERID=; Expires=Thu, 01-Jan-1970 00:00:10 GMT;"),
              ("Set-Cookie", "PASSHASH=; Expires=Thu, 01-Jan-1970 00:00:10 GMT;")])
              
def forgot_post(environ, start_response):
    request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    request_body = environ['wsgi.input'].read(request_body_size)
    options = parse_qs(request_body)
     
    email = options.get("email", [""])[0]
    q = database.execute("SELECT user_id, username FROM users WHERE email = ?", (email,)).fetchone()
    if not q:
        start_response(*redirect_header("/login.html"))
    else:
        send_lostpassword(q["username"], q["user_id"], email)
      
        start_response(*redirect_header("/login.html"))
 
def reset_post(environ, start_response):
      request_body_size = int(environ.get('CONTENT_LENGTH', 0))
      request_body = environ['wsgi.input'].read(request_body_size)
      options = parse_qs(request_body)
     
      key = options.get("key", [""])[0]
      password = options.get("password", [""])[0]
      password_verify = options.get("password", ["", ""])[1]
      
      if key not in forgot_links or password != password_verify:
          start_response(*redirect_header(URL + key))
      else:
          user_id = forgot_links[key]
          print user_id
          database.execute("UPDATE users SET pass_hash = ? WHERE user_id = ?", (sha512(password).hexdigest(), user_id))
          del forgot_links[key]
          start_response(*redirect_header("/login.html")) 

def register_post(environ, start_response):
      request_body_size = int(environ.get('CONTENT_LENGTH', 0))
      request_body = environ['wsgi.input'].read(request_body_size)
      options = parse_qs(request_body)

      username = options.get("username", [""])[0]
      password = options.get("password", [""])[0]
      password_verify = options.get("password", ["", ""])[1]
      email = options.get("email", [""])[0]
      
      if password != password_verify:
         start_response(*redirect_header("/register.html?prompt=mismatch"))
      elif not username or not password or not email:
         start_response(*redirect_header("/register.html?prompt=blank"))
      elif len(username) < 5 or len(password) < 6:
         start_response(*redirect_header("/register.html?prompt=length"))
      elif not validate_email(email):
         start_response(*redirect_header("/register.html?prompt=email"))
      else:
         q = database.execute("SELECT user_id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
         if q:
            start_response(*redirect_header("/register.html?prompt=duplicate"))
         else:
            database.execute("INSERT INTO users VALUES (NULL, ?, ?, ?, 0)", (username, sha512(password).hexdigest(), email))
            
            #FIXME This is possibly incorrect the "lastrowid" may not be the user_id
            send_confirmation(username, database.lastrowid, email)
            
            #TODO check that this actually worked
            #TODO add javascript to redirect to login if successful
            start_response(*redirect_header("/register.html?prompt=success"))

def index(environ, start_response):
   page_name = environ["PATH_INFO"]
   
   page = templates["index"].format(posts = compose_posts() or 'None',
                                    login_link=templates["login_link"] if not is_login(environ) 
                                    else templates["logout_link"].format(username=is_login(environ)[1]))
   
   start_response(*default_header(page_name, page))
   return page

def login(environ, start_response):
    page_name = environ["PATH_INFO"]
    qs = parse_qs(environ["QUERY_STRING"])

    prompts = defaultdict(str, { 
        "restricted" : "You must login to complete this action</br>",
        "unverified" : "You must verify your account before you can login</br>",
        "verified" : "You have successfully verified your account. Please login</br>",
        "failed" : "Invalid username or password</br>"
    })

    page = templates["login"].format(prompt=prompts[qs.get("prompt", [None])[0]])
    start_response(*default_header(page_name, page))
    return page

def register(environ, start_response):
    page_name = environ["PATH_INFO"]
    qs = parse_qs(environ["QUERY_STRING"])
    
    prompts = defaultdict(str, { 
        "success" : "Registration successful</br>",
        "blank" : "Username, password, and email must be non-empty</br>",
        "mismatch" : "Password and verification must match</br>",
        "duplicate" : "A user with that name or email is already registered</br>",
        "length" : "Username must be more than 5 characters, password must be more than 6</br>",
        "email" : "Invalid email address"
    })

    page = templates["register"].format(prompt=prompts[qs.get("prompt", [None])[0]])
    start_response(*default_header(page_name, page))
    return page
    
def verify(environ, start_response):
    page_name = environ["PATH_INFO"]
    if page_name in verify_links:
        database.execute("UPDATE users SET verified = 1 WHERE user_id = ?", (verify_links[page_name],))
        del verify_links[page_name]
        start_response(*redirect_header("/login.html?prompt=verified")) 
    else:
        start_response(*redirect_header("/login.html"))

def forgot(environ, start_response):
    page_name = environ["PATH_INFO"]
    page = templates["forgot"]
    start_response(*default_header(page_name, page))
    return page

def reset(environ, start_response):
    page_name = environ["PATH_INFO"]
    if page_name in forgot_links:
        page = templates["reset"].format(key=page_name)
        page_name += ".html"
        start_response(*default_header(page_name, page))
        return page
    else:
        start_response(*redirect_header("/login.html"))

def default(environ, start_response):
    page_name = environ["PATH_INFO"]
    page = open(page_name[1:]).read()
    start_response(*default_header(page_name, page))
    return page

def not_found(environ, start_response):
    page_name = environ["PATH_INFO"]
    page = templates["404"]
    start_response( '404 NOT FOUND', [('Content-Type', 'text/html'),
                                      ('Content-Length', str(len(page)))])
    
urls = [
    (r'^/verify/.+', verify),
    (r'^/forgot\.html.*', forgot),
    (r'^/forgot$', forgot_post),
    (r'^/login$', login_post),
    (r'^/forgot/reset$', reset_post),
    (r'^/forgot/.+', reset),
    (r'^/register\.html.*', register),
    (r'^/register$', register_post),
    (r'^/login\.html.*', login),
    (r'^/index\.html.*', index),
    (r'^$', index),
    (r'^/$', index),
    (r'^/logout$', logout),
    (r'^/new_post$', new_post),
    
    #TODO these should only appear at the end of URL
    (r'(\.js|\.css|\.jpg|\.png)', default),
    
    #Anything else should 404
    (r'.*', not_found)
    ]

def application(environ, start_response):
   path = environ["PATH_INFO"]
   response_body = ""

   try:
      for regex, callback in urls:
        match = re.search(regex, path)
        if match is not None:
            response_body = callback(environ, start_response) or ""
            break
    
   except IOError:
      response_body = templates["404"]
      status = '404 NOT FOUND'
      response_headers = [('Content-Type', 'text/html'),
                          ('Content-Length', str(len(response_body)))]

   return [response_body]

httpd = make_server(parsed_MAIN_URL.hostname, parsed_MAIN_URL.port, application)
httpd.serve_forever()
