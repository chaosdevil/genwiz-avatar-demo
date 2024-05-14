import smtplib, ssl


def send_email():
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "liubei.dw7@gmail.com"  # Enter your address
    receiver_email = "yok.sura@hotmail.com"  # Enter receiver address
    password = "spvl mrur psjk kstl"
    message = """\
    Subject: Hi there

    This message is sent from Python."""

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
        print("Send email")