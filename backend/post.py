
from settings import *
from database import *
from login import *
from markup import *

def add_post(user_id, post, unescaped):
   database.execute("INSERT INTO comments VALUES(NULL, ?, ?, ?)",
                    (user_id[0], post, unescaped))

def compose_posts():
   posts = database.execute("SELECT users.username, comments.body FROM users, comments WHERE comments.user_id = users.user_id").fetchall()
   return "".join([templates["post"].format(username=post['username'],
                                            content=post['body']) for post in posts])      
                    
def new_post(request):
    user = is_login(request.environ)
    if user:
        new_post = request.options.get("new_post", [""])[0]

        # Always escape user input to avoid script injection
        #TODO store the unmodified version to allow edits
        unescaped = new_post
        new_post = parse_markup(escape(new_post))

        add_post(user, new_post, unescaped)
        return request.redirect_response("/index.html")
    else:
       return request.redirect_response("/login.html?prompt=restricted")

