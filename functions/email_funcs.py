import re, os

def is_valid_email(email, domains):
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    username, domain_name = email.split("@")
    if domain_name not in domains:
        return False
    return True


sender_email = "verify@devh.in"
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "s4tyendra"
smtp_password = "grtcoffxecgsycbg" #os.getenv("SMTP_PASS", "vydaxnyxyvprmctp")

def send_otp(receiver_email, otp):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Your OTP"

    message.attach(MIMEText(f"<strong><b><h3>Your OTP is {otp}</b></h3></strong><ul><li>Will expire in 5 mins</li></ul>", "html"))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
    return True
