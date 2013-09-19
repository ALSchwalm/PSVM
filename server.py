#!/usr/bin/env python

from wsgiref.simple_server import make_server
from cgi import parse_qs, escape

posts = ""

def add_post(post):
   global posts
   if post:
      #This will eventually be put in the database
      posts += open("post.html").read().format(content=post)

   
def application(environ, start_response):
   global posts
   
   # the environment variable CONTENT_LENGTH may be empty or missing
   try:
      request_body_size = int(environ.get('CONTENT_LENGTH', 0))
   except (ValueError):
      request_body_size = 0 

   # When the method is POST the query string will be sent
   # in the HTTP request body which is passed by the WSGI server
   # in the file like wsgi.input environment variable.
   request_body = environ['wsgi.input'].read(request_body_size)
   d = parse_qs(request_body)

   post = d.get('new_post', [''])[0] # Returns the first age value.

   # Always escape user input to avoid script injection
   post = escape(post)

   add_post(post)

   #FIXME make this safer
   response_body = open(environ["PATH_INFO"][1:]).read().format(posts = posts or 'None')

   status = '200 OK'

   response_headers = [('Content-Type', 'text/html'),
                       ('Content-Length', str(len(response_body)))]
   start_response(status, response_headers)

   return [response_body]

httpd = make_server('localhost', 8051, application)
httpd.serve_forever()
