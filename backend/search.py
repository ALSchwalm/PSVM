
from database import *
from settings import *

def search(request):

    query = request.query_string.get("query", [""])[0]

    q = database.execute("""

    SELECT DISTINCT comments.thread_id,
                    title,
                    count(comments.thread_id) FROM comments
    LEFT OUTER JOIN
    threads ON
    threads.thread_id = comments.thread_id
    WHERE body LIKE ?
    GROUP BY comments.thread_id

    """, (r"%" + str(query) + r"%",)).fetchall()
    
    content = ""
    if query:
        for result in q:
            content += templates["search_link"].format(
                thread_id=result["thread_id"],
                title=result["title"],
                count=result[2])

    if content:
        page = templates["search"].format(results=content)
    elif query:
        page = templates["search"].format(results="No results found")
    else:
        page = templates["search"].format(results="")

    return request.default_response(page)

def search_post(request):
    query = request.options.get("query", [""])[0]
    
    return request.redirect_response("/search.html?query="+str(query))
