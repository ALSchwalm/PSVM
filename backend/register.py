
from collections import defaultdict

from settings import *
from mail import *
from database import *

def register_post(request):
      username = request.options.get("username", [""])[0]
      password = request.options.get("password", [""])[0]
      password_verify = request.options.get("password", ["", ""])[1]
      email = request.options.get("email", [""])[0]
      
      if password != password_verify:
         return request.redirect_response("/register.html?prompt=mismatch")
      elif not username or not password or not email:
         return request.redirect_response("/register.html?prompt=blank")
      elif len(username) < 5 or len(password) < 6:
         return request.redirect_response("/register.html?prompt=length")
      elif not validate_email(email):
         return request.redirect_response("/register.html?prompt=email")
      else:
         q = database.execute("SELECT user_id FROM users WHERE username = ? OR email = ?", (username, email)).fetchone()
         if q:
            return request.redirect_response("/register.html?prompt=duplicate")
         else:
            database.execute("INSERT INTO users VALUES (NULL, ?, ?, ?,0, 0)", (username, sha512(password).hexdigest(), email))
            
            #FIXME This is possibly incorrect the "lastrowid" may not be the user_id
            send_confirmation(username, database.lastrowid, email)
            
            #TODO check that this actually worked
            return request.redirect_response("/register.html?prompt=success")


def register(request):
    prompts = defaultdict(str, { 
        "success" : "Registration successful</br>",
        "blank" : "Username, password, and email must be non-empty</br>",
        "mismatch" : "Password and verification must match</br>",
        "duplicate" : "A user with that name or email is already registered</br>",
        "length" : "Username must be more than 5 characters, password must be more than 6</br>",
        "email" : "Invalid email address"
    })

    page = templates["register"].format(prompt=prompts[request.query_string.get("prompt", [None])[0]])
    return request.default_response(page)

def verify(request):
    if request.page_name in verify_links:
        database.execute("UPDATE users SET verified = 1 WHERE user_id = ?", (verify_links[request.page_name],))
        del verify_links[request.page_name]
        return request.redirect_response("/login.html?prompt=verified") 
    else:
       return request.redirect_response("/login.html") 
