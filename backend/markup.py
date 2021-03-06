import re

from xml.sax.saxutils import unescape
from database import *

SUPPORTED_LANGUAGES = ("cpp", "python", "perl", "ruby")

def parse_markup(comment_body):
    for language in SUPPORTED_LANGUAGES:
        
        groups = re.findall(r"\[code\]\({lang}\).*?\[\\code\]".format(lang=language),
                             comment_body,
                             flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)

        for group in groups:
            sample_body = re.findall(r"\[code\]\(.+?\)(?:\n)?(.*?)(?:\n)?\[\\code\]",
                                     group,
                                     flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)[0]

            database.execute('''

            INSERT INTO code_samples VALUES (NULL, ?, ?, ?)

            ''', (language, unescape(sample_body.strip()), sample_body))
            
            id = database.lastrowid
            
            comment_body = re.sub(r"\[code\]\({lang}\)(?:\n)?(.*?)(?:\n)?\[\\code\]".format(lang=language), 
                                  r'''<div class="code_sample" value="{id}"><pre class="brush: {lang};">\1</pre><a href="javascript:void(0)" class="execute_link">Execute</a></div>'''.format(
                                      lang=language,
                                      id=id), 
                                  comment_body,
                                  count = 1,
                                  flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)

    comment_body = re.sub(r"\[link\]\s*\((.*?)\)(.*?)\[\\link\]", 
                          r'<a href=\1>\2</a>',
                          comment_body,
                          flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)

    comment_body = re.sub(r"\[image\]\s*\((.*?)\)\s*\[\\image\]",
                          r'<img class="user_image" src="\1">',
                          comment_body,
                          flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    
    comment_body = re.sub(r"\n", "</br>", comment_body)

    return comment_body
