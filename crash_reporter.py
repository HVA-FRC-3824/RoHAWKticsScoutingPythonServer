import smtplib
import threading


emails = ['akmessing1@yahoo.com']
gmail_user = ''
password = ''

# https://www.raspberrypi.org/forums/viewtopic.php?f=29&t=69286
# TODO: setup texting when server crashes
mobiles = ['8659631368']


class EmailThread(threading.Thread):
    def reportServerCrash(self, message):
        smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo()
        smtpserver.login(gmail_user, password)
        header = 'To:' + ', '.join(emails) + '\n' + 'From: ' + gmail_user + '\n' + 'Subject: Server Crash \n'
        msg = header + '\n' + message
        smtpserver.sendmail(gmail_user, emails, msg)
        smtpserver.close()
