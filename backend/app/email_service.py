import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .config import settings

def send_email(recipient:str, subject:str, html:str):
    if not settings.email_password:
        print(f"[EMAIL DEMO] To={recipient} Subject={subject}"); return
    msg=MIMEMultipart("alternative"); msg["Subject"]=subject; msg["From"]=settings.email_from; msg["To"]=recipient
    msg.attach(MIMEText(html,"html"))
    with smtplib.SMTP(settings.email_host,settings.email_port) as s:
        s.starttls(); s.login(settings.email_username,settings.email_password); s.sendmail(settings.email_from,recipient,msg.as_string())

def send_verification_email(recipient,name,token):
    url=f"{settings.frontend_url}/verify.html?token={token}"
    send_email(recipient,"Verify your Kisan2Consumer account",f"<h2>Welcome {name}!</h2><p><a href='{url}'>Verify your email</a></p><p>Expires in 30 minutes.</p>")

def send_order_confirmation_to_farmer(recipient,farmer_name,order_id,product_name,quantity):
    send_email(recipient,f"New Kisan2Consumer order #{order_id}",f"<h2>New order</h2><p>Hello {farmer_name}, order #{order_id} contains {quantity} unit(s) of {product_name}.</p>")

def send_reset_email(recipient,token):
    url=f"{settings.frontend_url}/reset-password.html?token={token}"
    send_email(recipient,"Reset your Kisan2Consumer password",f"<p><a href='{url}'>Reset password</a></p>")
