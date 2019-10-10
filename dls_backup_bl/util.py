import smtplib
from datetime import datetime
from multiprocessing import Queue
from threading import Thread

from time import time
from os import path, makedirs

from dls_pmacanalyse import ConfigError


def time_stamp():
    return datetime.fromtimestamp(time()).strftime("%Y%m%d")


def mkdir_p(p):
    if p is not None:
        if not path.exists(p):
            makedirs(p)
        elif not path.isdir(p):
            raise ConfigError(
                'Backup path exists but is not a directory: %s' % path)


class Worker(Thread):
    # Thread executing jobs from a given queue
    def __init__(self, tasks):
        Thread.__init__(self)
        self.Jobs = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, arguments, k_args = self.Jobs.get()
            try:
                func(*arguments, **k_args)
            except Exception as err:
                print(err)
            self.Jobs.task_done()


class EmailMessage:
    def __init__(self):
        self.Message = ""

    def add_to_message(self, line):
        self.Message += "\n" + line

    def print_message(self):
        return self.Message


def send_email(sender, recipient, subject, email_text):
    # Diamond SMTP Address = outbox.rl.ac.uk
    ServerURL = 'outbox.rl.ac.uk'
    email_header = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (
        sender, recipient, subject)
    email_message = email_header + email_text
    MailServer = smtplib.SMTP(ServerURL)
    # mailServer.set_debuglevel(1)
    MailServer.sendmail(sender, recipient, email_message)
    MailServer.quit()
