
from settings import *
from database import *
from mail import *

def forgot_post(request):
    email = request.options.get("email", [""])[0]
    q = database.execute("SELECT user_id, username FROM users WHERE email = ?", (email,)).fetchone()
    if not q:
        return request.redirect_response("/login.html")
    else:
        send_lostpassword(q["username"], q["user_id"], email)

        return request.redirect_response("/login.html")
 
def reset_post(request):
      key = request.options.get("key", [""])[0]
      password = request.options.get("password", [""])[0]
      password_verify = request.options.get("password", ["", ""])[1]
      
      if key not in forgot_links or password != password_verify:
         return request.redirect_response(URL + key)
      else:
          user_id = forgot_links[key]
          
          database.execute("UPDATE users SET pass_hash = ? WHERE user_id = ?", (sha512(password).hexdigest(), user_id))
          del forgot_links[key]
          return request.redirect_response("/login.html")

def forgot(request):
    page = templates["forgot"]
    return request.default_response(page)

def reset(request):
    if request.page_name in forgot_links:
        page = templates["reset"].format(key=request.page_name)
        request.page_name += ".html"
        return request.default_response(page)
    else:
       return request.redirect_header("/login.html")
