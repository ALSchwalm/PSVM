import urllib
import urllib2
import re

from database import *
from collections import defaultdict
from xml.sax.saxutils import escape

EXECUTE_URL = 'http://codepad.org'

values = {'run' : True,
          'submit':'Submit'}

LANGUAGE_MAP = defaultdict(str, {
    "python" : "Python",
    "cpp" : "C++",
    "perl" : "Perl", 
    "ruby" : "Ruby"
})

def execute(request):

    id = re.findall(r'/(\d+)$', request.page_name)[0]
    
    q = database.execute("SELECT language, raw FROM code_samples WHERE sample_id = ?", (id,))
    q = q.fetchone()

    if not q:
        return request.redirect_response("/404")

    #Unfortunately js format lib has different names for languages
    values['lang'] = LANGUAGE_MAP[q["language"]]
    values['code'] = q["raw"]

    data = urllib.urlencode(values)
    
    req = urllib2.Request(EXECUTE_URL, data)
    response = urllib2.urlopen(req)
    page = response.read()
    
    output = re.findall(r'Output:.*<pre>\n(.*?)</pre>',
                        page,
                        re.MULTILINE | re.DOTALL)
    
    if output:
        output = output[0]
    else:
        return request.default_response("No output")        
    
    return request.default_response(parse_execute(output))

def parse_execute(output):
    output = re.sub(r"\n", "</br>", output)
    return output
