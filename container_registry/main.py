from email.message import EmailMessage
import smtplib ,ssl
import datetime
import time
print(datetime.datetime.now())
print('Sending Mail')
msg = EmailMessage()
msg.set_content('This is my message')
msg['Subject'] = 'Hello'
msg['From'] = 'abdbakroo@gmail.com'
msg['To'] = ['abdbakroo@gmail.com']
context=ssl.create_default_context()
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls(context=context)
server.login('abdbakroo@gmail.com', 'shxmpbgouxltzptq')
server.send_message(msg)
print('Mail Sent')
