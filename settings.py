from urlparse import urlparse

#To fix slow load times on windows with localhost see http://stackoverflow.com/a/1813778
URL = "http://localhost:8051" #pluto.cse.msstate.edu:10062
parsed_MAIN_URL = urlparse(URL)