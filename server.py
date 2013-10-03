#!/usr/bin/env python

from wsgiref.simple_server import make_server
from cgi import parse_qs, escape
from hashlib import sha512
from Cookie import SimpleCookie
from collections import defaultdict

from markup import parse_markup
from settings import *
from database import *
from mail import *
from request import *

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
                                            
def new_post(request):
    user = is_login(request.environ)
    if user:
        new_post = request.options.get("new_post", [""])[0]

        # Always escape user input to avoid script injection
        #TODO store the unmodified version to allow edits
        new_post = parse_markup(escape(new_post))

        add_post(user, new_post)
        return request.redirect_response("/index.html")
    else:
       return request.redirect_response("/login.html?prompt=restricted")

def login_post(request):
      username = request.options.get("username", [""])[0]
      password = request.options.get("password", [""])[0]
      
      #Basic SQL inject detection
      if username and (username[0] in ('"', "'") or password[0] in ('"', "'")):
        return request.response('301 REDIRECT', [('Location', "http://www.youtube.com/embed/rhr44HD49-U?autoplay=1&loop=1&playlist=rhr44HD49-U&showinfo=0")])
      
      q = database.execute("SELECT user_id, pass_hash, verified FROM users WHERE username = ? AND pass_hash = ?", (username, sha512(password).hexdigest()))
      result = q.fetchone()
      
      if not result or not username or not password:
         return request.redirect_response("/login.html?prompt=failed")
      elif result["verified"] != True:
         return request.redirect_response("/login.html?prompt=unverified")
      else:
         return request.response("301 REDIRECT", [('Location', URL + "/index.html"),
                                                  ("Set-Cookie", "USERID="+str(result["user_id"])),
                                                  ("Set-Cookie", "PASSHASH="+str(result["pass_hash"]))])

def logout(request):
   return request.response("301 REDIRECT", [('Location', URL + "/index.html"),
                                            ("Set-Cookie", "USERID=; Expires=Thu, 01-Jan-1970 00:00:10 GMT;"),
                                            ("Set-Cookie", "PASSHASH=; Expires=Thu, 01-Jan-1970 00:00:10 GMT;")])
              
def forgot_post(request):
    email = request.options.get("email", [""])[0]
    q = database.execute("SELECT user_id, username FROM users WHERE email = ?", (email,)).fetchone()
    if not q:
        return request.redirect_response("/login.html")
    else:
        send_lostpassword(q["username"], q["user_id"], email)
      
        return request.redirect_response("/login.html")
 
def reset_post(request):
      key = request.options.get("key", [""])[0]
      password = request.options.get("password", [""])[0]
      password_verify = request.options.get("password", ["", ""])[1]
      
      if key not in forgot_links or password != password_verify:
         return request.redirect_response(URL + key)
      else:
          user_id = forgot_links[key]
          
          database.execute("UPDATE users SET pass_hash = ? WHERE user_id = ?", (sha512(password).hexdigest(), user_id))
          del forgot_links[key]
          return request.redirect_response("/login.html")

def register_post(request):
      username = request.options.get("username", [""])[0]
      password = request.options.get("password", [""])[0]
      password_verify = request.options.get("password", ["", ""])[1]
      email = request.options.get("email", [""])[0]
      
      if password != password_verify:
         return request.redirect_response("/register.html?prompt=mismatch")
      elif not username or not password or not email:
         return request.redirect_response("/register.html?prompt=blank")
      elif len(username) < 5 or len(password) < 6:
         return request.redirect_response("/register.html?prompt=length")
      elif not validate_email(email):
         return request.redirect_response("/register.html?prompt=email")
      else:
         q = database.execute("SELECT user_id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
         if q:
            return request.redirect_response("/register.html?prompt=duplicate")
         else:
            database.execute("INSERT INTO users VALUES (NULL, ?, ?, ?, 0)", (username, sha512(password).hexdigest(), email))
            
            #FIXME This is possibly incorrect the "lastrowid" may not be the user_id
            send_confirmation(username, database.lastrowid, email)
            
            #TODO check that this actually worked
            #TODO add javascript to redirect to login if successful
            return request.redirect_response("/register.html?prompt=success")

def index(request):
   page = templates["index"].format(posts = compose_posts() or 'None',
                                    login_link=templates["login_link"] if not is_login(request.environ) 
                                    else templates["logout_link"].format(username=is_login(request.environ)[1]))
   
   return request.default_response(page)

def redirect_index(request):
   return request.redirect_response("/index.html")
   

def login(request):
    prompts = defaultdict(str, { 
        "restricted" : "You must login to complete this action</br>",
        "unverified" : "You must verify your account before you can login</br>",
        "verified" : "You have successfully verified your account. Please login</br>",
        "failed" : "Invalid username or password</br>"
    })

    page = templates["login"].format(prompt=prompts[request.query_string.get("prompt", [None])[0]])
    return request.default_response(page)

def register(request):
    prompts = defaultdict(str, { 
        "success" : "Registration successful</br>",
        "blank" : "Username, password, and email must be non-empty</br>",
        "mismatch" : "Password and verification must match</br>",
        "duplicate" : "A user with that name or email is already registered</br>",
        "length" : "Username must be more than 5 characters, password must be more than 6</br>",
        "email" : "Invalid email address"
    })

    page = templates["register"].format(prompt=prompts[request.query_string.get("prompt", [None])[0]])
    return request.default_response(page)
    
def verify(request):
    if request.page_name in verify_links:
        database.execute("UPDATE users SET verified = 1 WHERE user_id = ?", (verify_links[request.page_name],))
        del verify_links[request.page_name]
        return request.redirect_response("/login.html?prompt=verified") 
    else:
       return request.redirect_response("/login.html") 


def forgot(request):
    page = templates["forgot"]
    return request.default_response(page)

def reset(request):
    if request.page_name in forgot_links:
        page = templates["reset"].format(key=request.page_name)
        request.page_name += ".html"
        return request.default_response(page)
    else:
       return request.redirect_header("/login.html")

def default(request):
    page = open(request.page_name[1:]).read()
    return request.default_response(page)

def not_found(request):
    page = templates["404"]
    return request.response('404 NOT FOUND', [('Content-Type', 'text/html'),
                                              ('Content-Length', str(len(page)))],
                            page)
    
urls = [
    (r'^/verify/[0-9a-f]{128}$', verify),
    (r'^/forgot\.html(\?.*|$)', forgot),
    (r'^/forgot$', forgot_post),
    (r'^/login$', login_post),
    (r'^/forgot/reset$', reset_post),
    (r'^/forgot/[0-9a-f]{128}$', reset),
    (r'^/register\.html(\?.*|$)', register),
    (r'^/register$', register_post),
    (r'^/login\.html(\?.*|$)', login),
    (r'^/index\.html(\?.*|$)', index),
    (r'^$', redirect_index),
    (r'^/$', redirect_index),
    (r'^/logout$', logout),
    (r'^/new_post$', new_post),
    
    (r'(\.js|\.css|\.jpg|\.png)$', default),
    
    #Anything else should 404
    (r'.*', not_found)
    ]

def application(environ, start_response):
   path = environ["PATH_INFO"]
   response_body = ""
   r = Request(environ, start_response)
   
   try:
      for regex, callback in urls:
        match = re.search(regex, path)
        if match is not None:
           response_body = callback(r) or ""
           break
    
   except IOError:
      response_body = templates["404"]
      status = '404 NOT FOUND'
      response_headers = [('Content-Type', 'text/html'),
                          ('Content-Length', str(len(response_body)))]

   return [response_body]

httpd = make_server(parsed_MAIN_URL.hostname, parsed_MAIN_URL.port, application)
httpd.serve_forever()
