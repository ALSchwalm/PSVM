from xml.sax.saxutils import escape
from database import *
from settings import *

def search(request):

    query = escape(request.query_string.get("query", [""])[0])

    q = database.execute("""

    SELECT DISTINCT comments.thread_id,
                    title,
                    count(comments.thread_id),
                    threads.category_id,
                    name FROM comments
    LEFT OUTER JOIN
    threads ON
    threads.thread_id = comments.thread_id
    LEFT OUTER JOIN
    categories ON
    threads.category_id = categories.category_id
    WHERE raw LIKE ?
    GROUP BY comments.thread_id
    ORDER BY count(comments.thread_id) DESC

    """, (r"%" + str(query) + r"%",)).fetchall()
    
    content = ""
    if query and query != "%":
        for result in q:
            content += templates["search_link"].format(
                thread_id=result["thread_id"],
                title=result["title"],
                category=result["name"],
                category_id=result["category_id"],
                count=result[2])

    if content and query:
        page = templates["search"].format(results=content,
                                          title="Search results for '" + str(query) + "'")
    elif query:
        page = templates["search"].format(results="",
                                          title="No results found for '" + str(query) + "'")
    else:
        page = templates["search"].format(results="",
                                          title="")

    return request.default_response(page)

def search_post(request):
    query = escape(str(request.options.get("query", [""])[0]))

    return request.redirect_response("/search.html?query="+query)
