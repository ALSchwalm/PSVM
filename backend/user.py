from settings import *
from database import *
from post import *
from login import *

def profile(request):
    username = request.query_string.get("username", [""])[0]

    if not username:
        request.redirect_response("/404.html")
    
    q = database.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = q.fetchone()

    page = templates["profile"].format(
        username=username,
        email=user["email"])

    return request.default_response(page)
    
