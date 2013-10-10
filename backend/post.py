
from settings import *
from database import *
from login import *
from markup import *

def add_post(thread_id, user_id, post, unescaped):
    
    #TODO add check for locked threads / noexistant threads
    database.execute("INSERT INTO comments VALUES(NULL, ?, ?, ?, ?)",
                     (thread_id, user_id, post, unescaped))

#TODO add range
def compose_posts(thread_id, user_id):

    posts = database.execute("""

    SELECT * FROM users, comments
    WHERE comments.user_id = users.user_id AND comments.thread_id = ?

    """, (thread_id,)).fetchall()


    post_string = ""
    for post in posts:
        edit_button = ""
        if str(post["user_id"]) == str(user_id):
            edit_button = '<a href="javascript:void(0)">Edit</a>'
        post_string += templates["post"].format(username=post['username'],
                                                content=post['body'],
                                                post_id=post['comment_id'],
                                                edit=edit_button)
    return post_string
                    
def new_post(request):
    user = is_login(request.environ)
    if user:
        new_post = request.options.get("new_post", [""])[0]
        thread_id =request.options.get("thread_id", [""])[0] 
        
        # Always escape user input to avoid script injection
        #TODO store the unmodified version to allow edits
        unescaped = new_post
        new_post = parse_markup(escape(new_post))

        add_post(thread_id, user[0], new_post, unescaped)
        return request.redirect_response("/thread.html?thread_id="+thread_id)
    else:
       return request.redirect_response("/login.html?prompt=restricted")

def edit_post(request):
    user = is_login(request.environ)

    comment_id = re.findall(r'/edit/post_(\d+)$', request.page_name)[0] 
    
    q = database.execute("""

    SELECT user_id FROM comments WHERE comment_id = ?

    """, (comment_id,)).fetchone()

    #TODO check for admin edits
    if not q or not user or str(q["user_id"]) != user[0]:
        return request.redirect_response("404.html")

    edited_post = request.options.get("new_content", [""])[0]

    q = database.execute("""

    UPDATE comments SET body = ?, raw = ? WHERE comment_id = ? 

    """, (parse_markup(escape(edited_post)), edited_post, comment_id))
    
    return request.redirect_response(request.environ["HTTP_REFERER"])

def get_raw(request):
    comment_id = re.findall(r'/raw/post_(\d+)$', request.page_name)[0]
    
    q = database.execute("""

    SELECT raw FROM comments WHERE comment_id = ?

    """, (comment_id,)).fetchone()

    if not q:
        return request.default_response("")
    else:
        return request.default_response(str(q["raw"]))
