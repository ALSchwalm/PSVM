from cgi import parse_qs, escape
from mimetypes import guess_type
from settings import *
from login import *

class Request(object):
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response
        self.is_post = False
        
        if environ["REQUEST_METHOD"] == "POST":
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            request_body = environ['wsgi.input'].read(request_body_size)
            self.options = parse_qs(request_body)
            self.is_post = True
            
        else:
            self.options = []

        self.query_string = parse_qs(environ["QUERY_STRING"])
        self.page_name = environ["PATH_INFO"]
        

    def default_response(self, page):
        user = is_login(self.environ)

        if user:
            page = re.sub(r'(<ul id="title_links">.*?</ul>)',
                          r'''
                          <form action="/logout" method="post">
                          <ul id="title_links">
                          <li><a href="/index.html">Home</a></li>
                          <li><a href="/profile.html?username={username}">{username}</a></li>
                          <li><a href="javascript:void(0)" onclick="$(this).closest('form').submit();">Logout</a></li>
                          </ul></form>'''.format(
                              username=user[1]),
                          page,
                          flags=re.MULTILINE | re.DOTALL)
            
        
        status = '200 OK'
        
        #Determine MIME type
        mime = guess_type(self.page_name)[0] or "text/html" #default to text/html

        response_headers = [('Content-Type', mime),
                            ('Content-Length', str(len(page)))]

        self.start_response(status, response_headers)
        return page

    def redirect_response(self, address):
        self.start_response('301 REDIRECT', [('Location', URL + address)])

    def response(self, status, page_header, page=None):
        self.start_response(status, page_header)
        return page
