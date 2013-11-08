from settings import *
from database import *
from login import *

import os
import imghdr

def profile(request):
    username = request.query_string.get("username", [""])[0]
    
    prompt_map = {
        "size" : "Error: file size cannot exceed 4MB<br>",
        "filetype" : "Error: file must be an image<br>",
        "missing" : "Error: missing file in upload<br>"
    }

    prompt = prompt_map.get(request.query_string.get("prompt", [""])[0], "")

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
            prompt=prompt,
            picture="")
    else:
        page = templates["profile"].format(
            username=username,
            email=user["email"],
            joined=user["timestamp"],
            upload=upload,
            prompt=prompt,
            picture='<img id="profile_pic" src="/profile/{}.png">'.format(
                username))

    return request.default_response(page)
    
def profile_picture(request):
    user = is_login(request.environ)

    if not user:
        return request.redirect_response("/login.html?prompt=restricted")

    
    if request.fileitem.filename:

        #only allow recognized types
        if not imghdr.what("", request.fileitem.value):
            return request.redirect_response("/profile.html?username=" + str(user.username) +
                                             "&prompt=filetype")
        
        #File cannot be larger than 4MB
        elif int(request.environ.get('CONTENT_LENGTH', 0)) > 4000000:
            return request.redirect_response("/profile.html?username=" + str(user.username) +
                                             "&prompt=size")
            
        # strip leading path from file name to avoid directory traversal attacks
        fn = os.path.basename(os.path.splitext(request.fileitem.filename)[0])
        open('profile/' + user.username + ".png", 'wb').write(request.fileitem.file.read())

    else:
        return request.redirect_response("/profile.html?username=" + str(user.username) +
                                         "&prompt=missing")
        
    return request.redirect_response("/profile.html?username=" + str(user.username))
