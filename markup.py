import re

languages = ("cpp", "js")

def parse_markup(comment_body):
    for language in languages:
        comment_body = re.sub(r"\[code\]\({lang}\)(.*?)\[\\code\]".format(lang=language), 
                              r'<pre class="brush: {lang};">\1</pre>'.format(lang=language), 
                              comment_body,
                              flags=re.MULTILINE | re.DOTALL)
    return comment_body
