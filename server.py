#!/usr/bin/env python

from wsgiref.simple_server import make_server
from cgi import parse_qs, escape

#Go ahead and open the templates, we're bound to need them
templates = {"404" : open("404.html").read(),
             "index" : open("index.html").read(),
             "post" : open("post.html").read()}


#This will be in the database
posts = []

#these methods will hit the database 
def add_post(post):
   global posts
   posts.append(post)

def get_posts():
   global posts
   post_template = templates["post"]
   return "".join([post_template.format(content=body) for body in posts])
   
   
def application(environ, start_response):
   
   # the environment variable CONTENT_LENGTH may be empty or missing
   try:
      request_body_size = int(environ.get('CONTENT_LENGTH', 0))
   except (ValueError):
      request_body_size = 0 

   #Different handling for POST/GET. This prevents new posts on page refresh
   if environ["REQUEST_METHOD"] == "POST":
      request_body = environ['wsgi.input'].read(request_body_size)
      d = parse_qs(request_body)
      
      new_post = d.get('new_post', [''])[0]

      # Always escape user input to avoid script injection
      new_post = escape(new_post)

      add_post(new_post)

   #FIXME make this safer
   try:
      response_body = open(environ["PATH_INFO"][1:]).read().format(posts = get_posts() or 'None')
      status = '200 OK'
      
   except IOError:
      response_body = templates["404"]
      status = '404 File not found'

   #correct MIME type for js
   #TODO find a better way to do this
   if environ["PATH_INFO"][-3:] == ".js":
      response_headers = [('Content-Type', 'text/javascript'),
                          ('Content-Length', str(len(response_body)))]
   else:
      response_headers = [('Content-Type', 'text/html'),
                          ('Content-Length', str(len(response_body)))]
   start_response(status, response_headers)

   return [response_body]

httpd = make_server('localhost', 8051, application)
httpd.serve_forever()
