
from xml.sax.saxutils import escape
from settings import *
from database import *
from mail import *
from login import *


def message_thread(request):
    '''Messages from a particular user'''

    user = is_login(request.environ)
    from_id = request.query_string.get("username", [""])[0]
    
    if not user or not from_id:
        return request.redirect_response("/login.html?prompt=restricted")

    page = templates["message_thread"].format(
        body=compose_messages(user.user_id, from_id))
    

def messages(request):
    '''Overview of all messages for a user'''
    
    user = is_login(request.environ)

    if not user:
        return request.redirect_response("/login.html?prompt=restricted")
    
    page = templates["messages"].format(
        messages=compose_message_links(user.user_id))

    return request.default_response(page)

def compose_messages(to__id, from_id):
    '''Compose messages in a thread'''

    q = database.execute("""

    SELECT DISTINCT body, to_id, username FROM
    messages, users
    WHERE to_id = ? AND user_id = ?
    
    """, (to_id, from_id)).fetchall()

    messages_text = ""
    if q:
        for message in q:
            messages_text += templates["full_message"].format(
                username=message["username"],
                body=message["body"])

    return messages_text
    

def compose_message_links(user_id):
    '''Compose links to all messages to a user'''
    
    q = database.execute("""

    SELECT DISTINCT body, to_id, username FROM
    messages, users
    WHERE to_id = ? AND user_id = from_id
    
    """, (user_id,)).fetchall()

    messages_text = ""
    if q:
        for message in q:
            body = message["body"]
            if len(body) > 53:
                body = body[:50] + "..."
                
            messages_text += templates["message_link"].format(
                username=message["username"],
                body=body)
            messages_text += "<br/>"
        return messages_text
    else:
        return "None"

def message_post(request):
    user = is_login(request.environ)

    if not user:
        return request.redirect_response("404.html")

    body = request.options.get("message_body", [""])[0]
    from_id = user.user_id
    to_username = request.options.get("to_username", [""])[0]

    q = database.execute("""

    SELECT user_id FROM users WHERE username = ?

    """, (to_username,)).fetchone()

    if not q:
        return request.redirect_response("404.html")

    to_id = q["user_id"]
    
    database.execute("""

    INSERT INTO messages(message_id, body, from_id, to_id)
    VALUES(NULL, ?, ?, ?)

    """, (escape(body), from_id, to_id))
    
    #TODO redirect to correct place
    return request.redirect_response("index.html")
    
