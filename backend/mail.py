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

verify_links = {}
forgot_links = {}
random.seed()

def generate_link(user_id, prefix, link_dict):
    val = random.getrandbits(100)
    url =  prefix + str(sha512(str(val)).hexdigest())
    link_dict[url] = user_id
    return settings.URL + url

def validate_email(email):
    return True if EMAIL_VALIDATOR.match(email) else False
    
    
def send_confirmation(username, user_id, address):
    
    msg = MIMEText("""
    
    Hi {username}, 
    
    Thanks for registering at PSVM. To verify your account please click the following link:
    
    {link}
    """.format(username=username, link=generate_link(user_id, "/verify/", verify_links)))
    
    msg['Subject'] = "PSVM Registration"
    msg['From'] = FROM
    msg['To'] = address
    
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(USERNAME,PASSWORD)
    server.sendmail(FROM, address, msg.as_string())
    server.quit

def send_lostpassword(username, user_id, address):
    msg = MIMEText("""

    We received a notification that you lost your password. If you really wish to reset your password, please click the following link:
    
    {link}
    """.format(link=generate_link(user_id, "/forgot/", forgot_links)))
    
    msg['Subject'] = "PSVM Password Recovery"
    msg['From'] = FROM
    msg['To'] = address
    
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(USERNAME,PASSWORD)
    server.sendmail(FROM, address, msg.as_string())
    server.quit	


