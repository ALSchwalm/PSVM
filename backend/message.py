
from settings import *
from database import *
from mail import *
from login import *

def messages(request):
    user = is_login(request.environ)

    if not user:
        return request.redirect_response("/login.html?prompt=restricted")
    
    page = templates["messages"].format(
        messages=compose_messages(user[0]))

    return request.default_response(page)


def compose_messages(user_id):
    q = database.execute("""

    SELECT DISTINCT body, to_id, username FROM
    messages, users
    WHERE to_id = ? AND user_id = from_id
    
    """, (user_id,)).fetchall()

    messages_text = ""
    if q:
        for message in q:
            messages_text += templates["message_link"].format(
                username=message["username"],
                body=message["body"])
            messages_text += "<br/>"
        return messages_text
    else:
        return "None"

def message_post(request):
    user = is_login(request.environ)

    if not user:
        return request.redirect_response("404.html")

    body = request.options.get("message_body", [""])[0]
    from_id = user[0]
    to_username = request.options.get("to_username", [""])[0]

    q = database.execute("""

    SELECT user_id FROM users WHERE username = ?

    """, (to_username,)).fetchone()

    if not q:
        return request.redirect_response("404.html")

    to_id = q["user_id"]
    
    database.execute("""

    INSERT INTO messages VALUES(NULL, ?, ?, ?)

    """, (escape(body), from_id, to_id))
    print "Added {}, {}, {}".format(body, from_id, to_id)
    
    #TODO redirect to correct place
    return request.redirect_response("index.html")
    
