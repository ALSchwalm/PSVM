from urlparse import urlparse

#To fix slow load times on windows with localhost see http://stackoverflow.com/a/1813778
URL = "http://localhost:8051" #pluto.cse.msstate.edu:10062
parsed_MAIN_URL = urlparse(URL)


#Go ahead and open the templates, we're bound to need them
frame = open("templates/frame.html").read()

templates = {#open page templates
    "404" : frame.format(content=open("templates/404.html").read()),
    "index" : frame.format(content=open("templates/index.html").read()),
    "login" : frame.format(content=open("templates/login.html").read()),
    "register" : frame.format(content=open("templates/register.html").read()),
    "forgot" : frame.format(content=open("templates/forgot.html").read()),
    "reset" : frame.format(content=open("templates/reset_password.html").read()),
    "thread" : frame.format(content=open("templates/thread.html").read()),
    "new_thread" : frame.format(content=open("templates/new_thread.html").read()),
    "profile" : frame.format(content=open("templates/profile.html").read()),
    "category_page" : frame.format(content=open("templates/category_page.html").read()),
    "messages" : frame.format(content=open("templates/messages.html").read()),
    
             
    #open non-page templates - i.e. those not wrapped in the frame
    "login_link" : open("templates/login_link.html").read(),
    "logout_link" : open("templates/logout_link.html").read(),
    "thread_link" : open("templates/thread_link.html").read(),
    "post" : open("templates/post.html").read(),
    "category" : open("templates/category.html").read()}
