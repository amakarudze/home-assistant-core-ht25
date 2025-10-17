from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

gmail_user = "meenu2411as@gmail.com"  # config_entry.options
app_password = "nchk yflh zmdh ybdz"
to_email = "meenu2411as@gmail.com"

msg = MIMEMultipart()
msg["From"] = gmail_user
msg["To"] = to_email
msg["Subject"] = "Daily Reminder"
body = "Here is your Google Tasks to-do list for today."
msg.attach(MIMEText(body, "plain"))

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(gmail_user, app_password)
    server.sendmail(gmail_user, to_email, msg.as_string())
    server.quit()
    print("Email sent successfully!")
except Exception as e:
    print(f"Error: {e}")
