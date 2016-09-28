import smtplib
import json
import os

from googlevoice import Voice


class CrashReporter:
    def __init__(self, **kwargs):
        self.use_email = kwargs.get('use_email', True)
        self.emails = kwargs.get('emails', ['akmessing1@yahoo.com'])
        with open(('/').join(os.path.abspath(__file__).split('/')[:-1])+"/../server.json") as f:
            json_dict = json.loads(f.read())
        self.gmail_user = json_dict['gmail_user']
        self.gmail_password = json_dict['gmail_password']
        print(self.gmail_user)
        print(self.gmail_password)

        self.use_texting = kwargs.get('use_texting', True)
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
        header = ('To:' + ', '.join(self.emails) + '\n' + 'From: ' + self.gmail_user + '\n' +
                  'Subject: Server Crash!!! \n')
        msg = header + '\n' + message
        smtpserver.sendmail(self.gmail_user, self.emails, msg)
        smtpserver.close()

    def text_report(self, message):
        voice = Voice()
        voice.login(self.gmail_user, self.gmail_password)
        for phone_number in self.mobiles:
            voice.send_sms(phone_number, "Server Crash!!!\n{0:s}".format(message))
