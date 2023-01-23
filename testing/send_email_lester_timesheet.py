import smtplib, ssl
import os
from email.message import EmailMessage

port = 587  # For starttls
smtp_server = "smtp.gmail.com"
sender_email = "liusuqing97@gmail.com"

# Testing email
# receiver_email = "446751316@qq.com"

# Actual email
receiver_email = "timesheets@lester.com.au"
password = os.environ.get("PYTHON_EMAIL_PASSWORD")

# Dates to be checked
subject = 'Tax Invoice - Caxec Pty Ltd - Talenza/Macquarie'
body = f"""
Hi Lester team,

Please find the attached tax invoice for the fortnight 02/01/2023 - 15/01/2023.

Best Regards,
Felix
"""

em = EmailMessage()
em['From'] = sender_email
em['To'] = receiver_email
em['Subject'] = subject
em.set_content(body)

# Invoice name to be checked
invoice_name = 'Invoice Mac-20230116.pdf'
with open(f"E:\\files\\Company\\Caxec\\invoice\\unpaid\{invoice_name}", 'rb') as content_file:
    content = content_file.read()
    em.add_attachment(content, maintype='application', subtype='pdf', filename=f"{invoice_name}")

context = ssl.create_default_context()
with smtplib.SMTP(smtp_server, port) as server:
    server.ehlo() 
    server.starttls(context=context)
    server.ehlo() 
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, em.as_string()) 