import smtplib
# import threading


class CrashReporter:
    def __init__(self, **kwargs):
        self.use_email = kwargs.get('use_email', True)
        self.emails = kwargs.get('emails', ['akmessing1@yahoo.com'])
        self.gmail_user = kwargs.get('gmail_user', '')
        self.gmail_password = kwargs.get('gmail_password', '')

        # https://www.raspberrypi.org/forums/viewtopic.php?f=29&t=69286
        # TODO: setup texting when server crashes
        self.use_texting = kwargs.get('use_texting', False)
        self.mobiles = kwargs.get('mobiles', ['8659631368'])

    def report_server_crash(self, message):
        if self.use_email:
            self.email_report(message)

        if self.use_texting:
            self.text_report(message)

    def email_report(self, message):
        smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo()
        smtpserver.login(self.gmail_user, self.gmail_password)
        header = 'To:' + ', '.join(self.emails) + '\n' + 'From: ' + self.gmail_user + '\n' + 'Subject: Server Crash \n'
        msg = header + '\n' + message
        smtpserver.sendmail(self.gmail_user, self.emails, msg)
        smtpserver.close()

    def text_report(self, message):
        pass
