from settings import *
from database import *
from post import *
from login import *
from thread import *

def compose_category(category_id):
    q = database.execute("""

    SELECT DISTINCT threads.thread_id, threads.title, categories.name
    FROM threads INNER JOIN categories
    ON threads.category_id = categories.category_id
    WHERE categories.category_id = ?

    """, (category_id,))

    threads = q.fetchall()
    thread_names = ""

    if not threads:
        return ""

    for thread in threads:
        thread_id = thread["thread_id"]
        title = thread["title"]
        thread_names += templates["thread_link"].format(thread_id=thread_id, title=title)
        thread_names += "<br>"

    page = templates["category"].format(
        #FIXME
        category_name=threads[0]["name"],
        threads = thread_names)

    return page



def category(request):
    category_id = request.query_string.get("category_id", [""])[0]

    q = database.execute("""

    SELECT  name FROM categories
    WHERE category_id = ?

    """, (category_id,)).fetchone()

    if not q:
        return request.redirect_response("/404.html")

    page = frame.format(content=compose_category(category_id))

    return request.default_response(page)
    
    
