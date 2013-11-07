from settings import *
from database import *
from login import *

import os

def profile(request):
    username = request.query_string.get("username", [""])[0]

    q = database.execute("""

    SELECT email, timestamp FROM users
    WHERE username = ?

    """, (username,))
    
    user = q.fetchone()
    
    if not user or not username:
        return request.redirect_response("/404.html")

    upload = ""
    if is_login(request.environ).username == username:
        upload="""
  <form method="post" action="/profile_picture" enctype="multipart/form-data">
    <input type="file" name="file"><br>
    <input type="submit" value="Upload picture">
  </form>"""
    
    if not os.path.exists("profile/" + str(username) + ".png"):
        page = templates["profile"].format(
            username=username,
            email=user["email"],
            joined=user["timestamp"],
            upload=upload,
            picture="")
    else:
        page = templates["profile"].format(
            username=username,
            email=user["email"],
            joined=user["timestamp"],
            upload=upload,
            picture='<img id="profile_pic" src="/profile/{}.png">'.format(
                username))

    return request.default_response(page)
    
def profile_picture(request):
    user = is_login(request.environ)

    if not user:
        return request.redirect_response("/404.html")
    
    if request.fileitem.filename:
   
        # strip leading path from file name to avoid directory traversal attacks
        fn = os.path.basename(os.path.splitext(request.fileitem.filename)[0])
        open('profile/' + user.username + ".png", 'wb').write(request.fileitem.file.read())

    return request.redirect_response("/profile.html?username=" + str(user.username))
