from mail import *
from settings import *
from database import *
from post import *
from login import *


def compose_threads(category_id):
    q = database.execute("SELECT thread_id, title FROM threads WHERE category_id = ?", (category_id,))

    threads = q.fetchall()
    thread_names = ""
    
    for thread in threads:
        thread_id = thread["thread_id"]
        title = thread["title"]
        thread_names += templates["thread_link"].format(thread_id=thread_id, title=title)
        thread_names += "<br>"
        
    return thread_names

def new_thread(request):
    page = templates["new_thread"]
    return request.default_response(page)
    
def thread(request):
    thread_id = request.query_string.get("thread_id", [""])[0]

    q = database.execute("SELECT * FROM threads WHERE thread_id = ?", (thread_id,))
    q = q.fetchone()

    if not q:
        return request.redirect_response("/index.html")
    
    page = templates["thread"].format(thread_id=thread_id,
                                      posts=compose_posts(thread_id))

    return request.default_response(page)

def thread_post(request):
    title = request.options.get("title", [""])[0]
    
    if not is_login(request.environ):
        return request.redirect_response("/login.html?prompt=restricted")
    elif not request.is_post or not title:
        return request.redirect_response("/index.html")

    
    #TODO take category, etc in request
    q = database.execute("""INSERT INTO threads VALUES(NULL, 1, ?)""", (title,))

    return request.redirect_response("/thread.html?thread_id="+str(database.lastrowid))
