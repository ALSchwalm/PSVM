#!/usr/bin/env python

from wsgiref.simple_server import make_server

from backend import *

def index(request):
   page = templates["index"].format(threads=compose_threads("1") or 'None',
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
   (r'^/thread\.html(\?.*|$)', thread),
   (r'^/new_thread$', thread_post),
   (r'^/new_thread\.html(\?.*|$)', new_thread),
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

if __name__ == "__main__":
   httpd = make_server(parsed_MAIN_URL.hostname, parsed_MAIN_URL.port, application)
   httpd.serve_forever()
