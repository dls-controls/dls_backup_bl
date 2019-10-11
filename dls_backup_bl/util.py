import smtplib
from threading import Thread


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
    server_url = 'outbox.rl.ac.uk'
    email_header = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (
        sender, recipient, subject)
    email_message = email_header + email_text
    mail_server = smtplib.SMTP(server_url)
    # mailServer.set_debuglevel(1)
    mail_server.sendmail(sender, recipient, email_message)
    mail_server.quit()
