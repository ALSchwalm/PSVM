import re

from database import *

SUPPORTED_LANGUAGES = ("cpp", "js", "java", "python")

def parse_markup(comment_body):
    for language in SUPPORTED_LANGUAGES:
        
        groups = re.findall(r"\[code\]\({lang}\)(.*?)\[\\code\]".format(lang=language),
                             comment_body,
                             flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
        ids = []
        for group in groups:
            database.execute("INSERT INTO code_samples VALUES (NULL, ?)", (group,))
            ids.append(database.lastrowid)

        for id in ids:
            comment_body = re.sub(r"\[code\]\({lang}\)(.*?)\[\\code\]".format(lang=language), 
                                  r'<pre class="brush: {lang};" id="sample_{id}">\1</pre>'.format(lang=language, id=id), 
                                  comment_body,
                                  count = 1,
                                  flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)

    comment_body = re.sub(r"\[link\]\((.*?)\)(.*?)\[\\link\]", 
                          r'<a href=\1>\2</a>', 
                          comment_body,
                          flags=re.MULTILINE | re.DOTALL | re.IGNORECASE)
    comment_body = re.sub(r"\n", "</br>", comment_body)
    return comment_body