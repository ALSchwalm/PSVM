from collections import defaultdict, namedtuple
from Cookie import SimpleCookie
from hashlib import sha512

from mail import *
from settings import *
from database import *

login_info = namedtuple('LoginInfo', ['user_id', 'username', 'admin'])

def is_login(environ):
   try:
      c = SimpleCookie(environ.get("HTTP_COOKIE",""))
      user_id = c["USERID"].value
      password_hash = c["PASSHASH"].value

      user = database.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
      
      if not user or user['pass_hash'] != password_hash:
         return False
  
      return login_info(user_id, user["username"], user["admin"])

   except KeyError:
      return False


def login_post(request):
      username = request.options.get("username", [""])[0]
      password = request.options.get("password", [""])[0]
      
      #Basic SQL inject detection
      if username and (username[0] in ('"', "'") or password[0] in ('"', "'")):
         return request.response('301 REDIRECT', [('Location', "http://www.youtube.com/embed/rhr44HD49-U?autoplay=1&loop=1&playlist=rhr44HD49-U&showinfo=0")])
      
      q = database.execute("SELECT user_id, pass_hash, verified FROM users WHERE username = ? AND pass_hash = ?", (username, sha512(password).hexdigest()))
      result = q.fetchone()
      
      if not result or not username or not password:
         return request.redirect_response("/login.html?prompt=failed")
      elif result["verified"] != True:
         return request.redirect_response("/login.html?prompt=unverified")
      else:
         return request.response("301 REDIRECT", [('Location', URL + "/index.html"),
                                                  ("Set-Cookie", "USERID="+str(result["user_id"])),
                                                  ("Set-Cookie", "PASSHASH="+str(result["pass_hash"]))])

def login(request):
    prompts = defaultdict(str, { 
        "restricted" : "You must login to complete this action</br>",
        "unverified" : "You must verify your account before you can login</br>",
        "verified" : "You have successfully verified your account. Please login</br>",
        "failed" : "Invalid username or password</br>"
    })

    page = templates["login"].format(prompt=prompts[request.query_string.get("prompt", [None])[0]])
    return request.default_response(page)


def logout(request):
   return request.response("301 REDIRECT", [('Location', URL + "/index.html"),
                                            ("Set-Cookie", "USERID=; Expires=Thu, 01-Jan-1970 00:00:10 GMT;"),
                                            ("Set-Cookie", "PASSHASH=; Expires=Thu, 01-Jan-1970 00:00:10 GMT;")])
