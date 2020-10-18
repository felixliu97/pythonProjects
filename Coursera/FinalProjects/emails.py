from email.message import EmailMessage
import os.path
import mimetypes
import smtplib
import getpass

message = EmailMessage()
print(message)

sender = "me@example.com"
recipient = "liusuqing97@gmail.com"
message['From'] = sender
message['To'] = recipient

message['Subject'] = 'Greetings from {} to {}!'.format(sender, recipient)
body = """Hey there!

I'm learning to send emails using Python!"""
message.set_content(body)

# print(message)

attachment_path = "removed.png"
attachment_filename = os.path.basename(attachment_path)
mime_type, _ = mimetypes.guess_type(attachment_path)
# print(mime_type)

mime_type, mime_subtype = mime_type.split('/', 1)
# print(mime_type)
# print(mime_subtype)

with open(attachment_path, 'rb') as ap:
    message.add_attachment(ap.read(),
                           maintype=mime_type,
                           subtype=mime_subtype,
                           filename=os.path.basename(attachment_path))

# print(message)

mail_server = smtplib.SMTP_SSL('smtp.example.com')
mail_pass = getpass.getpass('Password? ')
mail_server.login(sender, mail_pass)

mail_server.send_message(message)
mail_server.quit()

