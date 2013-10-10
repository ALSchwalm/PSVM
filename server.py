#!/usr/bin/env python

from wsgiref.simple_server import make_server

from backend import *

def index(request):
   q = database.execute("""

   SELECT category_id FROM categories

   """).fetchall()

   categories_text = ""
   for category in q:
      categories_text += compose_category(category["category_id"])
      categories_text += "<br>"
   
   page = templates["index"].format(categories=categories_text or 'None')
   
   return request.default_response(page)

def redirect_index(request):
   return request.redirect_response("/index.html")
   
def default(request):
    page = open(request.page_name[1:], 'rb').read()
    return request.default_response(page)

def error_404(request):
    page = templates["404"]
    return request.response('404 NOT FOUND', [('Content-Type', 'text/html'),
                                              ('Content-Length', str(len(page)))],
                            page)

def favicon(request):
    return request.default_response("")

urls = [
   (r'^/verify/[0-9a-f]{128}$', verify),
   (r'^/forgot\.html(\?.*|$)', forgot),
   (r'^/forgot$', forgot_post),
   (r'^/login$', login_post),
   (r'^/forgot/reset$', reset_post),
   (r'^/forgot/[0-9a-f]{128}$', reset),
   (r'^/register\.html(\?.*|$)', register),
   (r'^/register$', register_post),
   (r'^/raw/\d+', get_raw),
   (r'^/execute/\d+', execute),
   (r'^/category\.html(\?.*|$)', category),
   (r'^/login\.html(\?.*|$)', login),
   (r'^/index\.html(\?.*|$)', index),
   (r'^/thread\.html(\?.*|$)', thread),
   (r'^/new_thread$', thread_post),
   (r'^/new_thread\.html(\?.*|$)', new_thread),
   (r'^/profile\.html(\?.*|$)', profile),
   (r'^/messages\.html(\?.*|$)', messages),
   (r'^/message$', message_post),
   (r'^$', redirect_index),
   (r'^/$', redirect_index),
   (r'^/logout$', logout),
   (r'^/new_post$', new_post),
   (r'^/edit/post_\d+', edit_post),
   (r'^/favicon\.ico$', favicon),
    
   (r'(\.js|\.css|\.jpg|\.png)$', default),
    
   #Anything else should 404
   (r'.*', error_404)
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
      response_body = error_404(r)
      
   return [response_body]

if __name__ == "__main__":
   httpd = make_server(parsed_MAIN_URL.hostname, parsed_MAIN_URL.port, application)
   httpd.serve_forever()
