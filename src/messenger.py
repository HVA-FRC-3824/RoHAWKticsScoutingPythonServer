import smtplib
import json
import os
from multiprocessing import Lock as PLock
from threading import Lock as TLock
from twilio.rest import TwilioRestClient
from decorator import type_check, attr_check, singleton
import logging
from ourlogging import setup_logging
setup_logging(__file__)
logger = logging.getLogger(__name__)


@singleton
class Messenger:
    '''Singleton that sends messages via email and text upon a crash

    Kwargs:
        use_email (`bool`): whether to send reports via email

        emails (`list`): list of emails to send reports to

        use_texting (`bool`): whether to send reports via texting

        mobiles (`list`): list of phone numbers to send reports to

        login_file (`str`): location of the file containing the login information (not in the repo)
    '''
    def __init__(self, **kwargs):
        if not hasattr(self, 'instance'):
            self.use_email = kwargs.get('use_email', True)
            self.use_texting = kwargs.get('use_texting', True)

            if self.use_email or self.use_texting:
                login_file_path = os.path.dirname(__file__) + "/" + kwargs.get('logins_file', '../../logins.json')
                if(not os.path.isfile(login_file_path)):
                    logger.error("Login file {0:s} does not exist".format(login_file_path))
                    # Real problem... no way to communicate
                    return
                f = open(login_file_path)
                json_dict = json.loads(f.read())

            if self.use_email:
                self.emails = kwargs.get('emails', ['akmessing1@yahoo.com'])
                self.gmail_user = json_dict['gmail_user']
                self.gmail_password = json_dict['gmail_password']

                self.smtp = smtplib.SMTP("smtp.gmail.com", 587)
                self.smtp.ehlo()
                self.smtp.starttls()
                self.smtp.ehlo()
                self.smtp.login(self.gmail_user, self.gmail_password)

            if self.use_texting:
                self.mobiles = kwargs.get('mobiles', ['8659631368'])

                self.twilio_sid = json_dict['twilio_sid']
                self.twilio_token = json_dict['twilio_token']
                self.twilio_number = json_dict['twilio_number']
                self.twilio = TwilioRestClient(self.twilio_sid, self.twilio_token)

            self.tlock = TLock()
            self.plock = PLock()

    @type_check
    def send_message(self, subject: str, message: str): -> None
        '''Send a message if the server crashed

        Args:
            message (`str`): error message to send
        '''
        self.tlock.acquire()
        self.plock.acquire()
        print("Sending message")
        if self.use_email:
            print("Sending email")
            self.email_report(subject, message)

        if self.use_texting:
            print("Sending text")
            self.text_report(subject)
        self.tlock.release()
        self.plock.release()

    @type_check
    def email_report(self, subject: str, message: str): -> None
        '''send the message via email

        Args:
            message (`str`): error message to send
        '''
        header = ("To:{0:s}\nFrom:{1:s}\nSubject: {2:s}\n"
                  .format(', '.join(self.emails), self.gmail_user, subject))
        msg = header + '\n' + message
        self.smtp.sendmail(self.gmail_user, self.emails, msg)

    @type_check
    def text_report(self, subject: str): -> None
        '''send the message via text

        Args:
            message (`str`): error message to send
        '''
        for phone_number in self.mobiles:
            self.twilio.messages.create(to=phone_number,
                                        from_=self.twilio_number,
                                        body="{0:s}\nCheck email for details".format(subject))
