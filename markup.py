import re

SUPPORTED_LANGUAGES = ("cpp", "js", "java", "python")

def parse_markup(comment_body):
    for language in SUPPORTED_LANGUAGES:
        comment_body = re.sub(r"\[code\]\({lang}\)(.*?)\[\\code\]".format(lang=language), 
                              r'<pre class="brush: {lang};">\1</pre>'.format(lang=language), 
                              comment_body,
                              flags=re.MULTILINE | re.DOTALL)
                              
    comment_body = re.sub(r"\n", "</br>", comment_body)
    return comment_body