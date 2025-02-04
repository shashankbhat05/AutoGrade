from datetime import datetime
import smtplib
from email.mime.text import MIMEText

sender = "pgbhatup@gmail.com"
password = "svfc mpvm argd mhfd"

def send_email(subject, body, recipients):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")

def getDateTime():
    # current date and time
    now = datetime.now()
    date_time = now.strftime("%d/%m/%Y, %H:%M:%S")
    # dd/mm/YY H:M:S format
    return date_time