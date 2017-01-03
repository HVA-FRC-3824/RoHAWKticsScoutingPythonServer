import smtplib
import json
import os
from multiprocessing import Lock as PLock
from threading import Lock as TLock

from googlevoice import Voice


class CrashReporter:
    shared_state = {}

    def __init__(self, **kwargs):
        self.__dict__ = self.shared_state
        if not hasattr(self, 'instance'):
            self.use_email = kwargs.get('use_email', True)
            self.emails = kwargs.get('emails', ['akmessing1@yahoo.com'])
            with open(os.path.dirname(__file__) +
                      kwargs.get('gmail_login', "../gmail_login.json")) as f:
                json_dict = json.loads(f.read())
            self.gmail_user = json_dict['gmail_user']
            self.gmail_password = json_dict['gmail_password']

            self.use_texting = kwargs.get('use_texting', True)
            self.mobiles = kwargs.get('mobiles', ['8659631368'])

            self.tlock = TLock()
            self.plock = PLock()

            self.instance = True

    def report_server_crash(self, message):
        self.tlock.acquire()
        self.plock.acquire()
        if self.use_email:
            self.email_report(message)

        if self.use_texting:
            self.text_report(message)
        self.tlock.release()
        self.plock.release()

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
