import smtplib
import random
import settings
import re

from hashlib import sha512
from email.mime.text import MIMEText

PASSWORD = open("credentials.key").read()
USERNAME = 'psvmmail'
FROM = 'psvmmail@gmail.com'

EMAIL_VALIDATOR = re.compile(r"[A-Za-z_\.0-9]+@[A-Za-z_\.0-9]+\.[A-Za-z]+")

live_links = {}
random.seed()

def generate_link(user_id):
    val = random.getrandbits(100)
    url =  "/verify/" + str(sha512(str(val)).hexdigest())
    live_links[url] = user_id
    return settings.URL + url

def validate_email(email):
    return True if EMAIL_VALIDATOR.match(email) else False
    
    
def send_confirmation(username, user_id, address):
    
    msg = MIMEText("""
    
    Hi {username}, 
    
    Thanks for registering at PSVM. To verify your accout please click the following link:
    
    {link}
    """.format(username=username, link=generate_link(user_id)))
    
    msg['Subject'] = "PSVM Registration"
    msg['From'] = FROM
    msg['To'] = address
    
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(USERNAME,PASSWORD)
    server.sendmail(FROM, address, msg.as_string())
    server.quit()