#!/usr/bin/env python

from wsgiref.simple_server import make_server
from cgi import parse_qs, escape
from hashlib import sha512
from Cookie import SimpleCookie
from collections import defaultdict

from backend import *

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

def add_post(user_id, post, unescaped):
   database.execute("INSERT INTO comments VALUES(NULL, ?, ?, ?)",
                    (user_id[0], post, unescaped))

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
        unescaped = new_post
        new_post = parse_markup(escape(new_post))

        add_post(user, new_post, unescaped)
        return request.redirect_response("/index.html")
    else:
       return request.redirect_response("/login.html?prompt=restricted")


def index(request):
   page = templates["index"].format(posts = compose_posts() or 'None',
                                    login_link=templates["login_link"] if not is_login(request.environ) 
                                    else templates["logout_link"].format(username=is_login(request.environ)[1]))
   
   return request.default_response(page)

def redirect_index(request):
   return request.redirect_response("/index.html")
   

def default(request):
    page = open(request.page_name[1:], 'rb').read()
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
   (r'^/execute/\d+', execute),
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
      response_body = not_found(r)
      
   return [response_body]

httpd = make_server(parsed_MAIN_URL.hostname, parsed_MAIN_URL.port, application)
httpd.serve_forever()
