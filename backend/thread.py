from mail import *
from settings import *
from database import *
from post import *
from login import *

def new_thread(request):
    q = database.execute("SELECT category_id, name FROM categories")
    q = q.fetchall()

    links = ""
    for category in q:
        links+='<option value="{id}"> {name} </option>'.format(
            id=category["category_id"],
            name=category["name"])
    
    page = templates["new_thread"].format(category_options=links)
    return request.default_response(page)
    
def thread(request):
    thread_id = request.query_string.get("thread_id", [""])[0]
    user = is_login(request.environ)
    
    q = database.execute("""

    SELECT * FROM threads, categories WHERE
    threads.thread_id = ? and categories.category_id = threads.category_id

    """, (thread_id,))
    
    q = q.fetchone()

    if not q:
        return request.redirect_response("/404.html")
    
    page = templates["thread"].format(thread_id=thread_id,
                                      posts=compose_posts(thread_id, user),
                                      category_id=q["category_id"],
                                      category_name=q["name"],
                                      thread_title=q["title"])

    return request.default_response(page)

def thread_post(request):
    title = request.options.get("title", [""])[0]
    new_post = request.options.get("new_post", [""])[0]
    category = request.options.get("category", ["1"])[0]

    user = is_login(request.environ)
    if not user:
        return request.redirect_response("/login.html?prompt=restricted")
    elif not request.is_post or not title:
        return request.redirect_response("/index.html")
    
    q = database.execute("""

    INSERT INTO threads VALUES(NULL, ?, ?, ?)

    """, (category, title, user.user_id))

    thread_id = database.lastrowid
    unescaped = new_post
    new_post = parse_markup(escape(new_post))

    add_post(thread_id, user.user_id, new_post, unescaped)
    
    return request.redirect_response("/thread.html?thread_id="+str(thread_id))
