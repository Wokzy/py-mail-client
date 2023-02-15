"""
Simple mail client based on SMTPlib and IMAPlib
SSL supported
Client is thread

Tested on greenmail/stanalone
"""

import time
import email
import queue
import smtplib
import imaplib
import threading

from config import SERVER_DOMAIN, SMTP_PORT, IMAP_PORT, MESSAGE_CHECK_COOLDOWN, \
					USE_SSL, LOGIN, PASSWORD, INBOX_FOLDER, INGNORE_ALREADY_RECIEVED_MESSAGES


__author__ = 'Yegor Yershov'



class MailClient(threading.Thread):
	def __init__(self, logging=False):
		"""
		Initting super, settings setting
		"""
		super().__init__(daemon=True)

		self.logging = logging
		self.new_emails_queue = queue.Queue()

		self.login = LOGIN
		self.password = PASSWORD
		self.use_ssl = USE_SSL

		self.inbox = [[], self.load_inbox()][INGNORE_ALREADY_RECIEVED_MESSAGES]
		self.catch = True


	def smtp_authorize(self):
		"""
		SMTP authorization to server
		"""

		if self.use_ssl:
			smtp = smtplib.SMTP_SSL(SERVER_DOMAIN, SMTP_PORT)
		else:
			smtp = smtplib.SMTP(SERVER_DOMAIN, SMTP_PORT)

		status = smtp.ehlo() # using ESMTP
		if status[0] != 250: # 250 means "everything is fine"
			raise RuntimeError(f'Server hello responce is {status[0]}: """{status[1].decode()}"""')

		#self.log(f'status: {status}')

		status = smtp.login(self.login, self.password)
		if status[0] != 235: # 235 means login is successfull
			raise RuntimeError(f'Server login failed: {status[1]}')

		#self.log('login is successful')
		return smtp


	def imap_authorize(self):
		"""
		IMAP authorization to server
		"""

		if self.use_ssl:
			imap = imaplib.IMAP4_SSL(host=SERVER_DOMAIN, port=IMAP_PORT)
		else:
			imap = imaplib.IMAP4(host=SERVER_DOMAIN, port=IMAP_PORT)

		status = imap.login(self.login, self.password)
		if status[0] != 'OK':
			raise RuntimeError(f'Server login failed: {status[1]}')

		return imap


	def log(self, message:str, priority:bool=False):
		"""
		Writes logs if they are turned on
		"""
		if self.logging or priority:
			print(f'[INFO] {message}')


	def send_message(self, reciever:str, message:str):
		"""
		Send direct message
		"""
		smtp = self.smtp_authorize()
		responce = smtp.sendmail(LOGIN, reciever, message)
		self.log(f'Message has been sent to {reciever} {responce}')


	def load_inbox(self):
		"""
		Returns list, containing "email.message.Message" structures fromed of messages from INBOX
		email.message.Message.items() - return all message add. info (subject, date)
												(use get_payload() to get payload)
		"""

		imap = self.imap_authorize()
		status, messages_indexes = imap.select(INBOX_FOLDER)
		messages_amount = int(messages_indexes[0])

		messages = []

		for i in range(messages_amount, 0, -1):
			message = imap.fetch(str(i), "(RFC822)")[1]
			for responce in message:
				if isinstance(responce, tuple):
					messages.append(email.message_from_bytes(responce[1]))

		return messages


	def find_new_messages(self, first:list, second:list):
		"""
		Iterates by lists of emails, comparing payloads and items
		"""

		new = []

		for mail in first:
			flag = True
			for mail2 in second:
				if mail.get_payload() == mail2.get_payload() and mail.items() == mail2.items():
					flag = False
					break

			if flag:
				new.append(mail)

		return new


	def run(self):
		"""
		Main thread function, updating inbox
		"""
		self.smtp_authorize()

		while self.catch:
			inbox = self.load_inbox()
			for mail in self.find_new_messages(inbox, self.inbox):
				self.new_emails_queue.put(mail)
				self.log('New message!')

			self.inbox = inbox

			time.sleep(MESSAGE_CHECK_COOLDOWN)


if __name__ == '__main__':
	main_thread = MailClient(logging=True) # console logging on
	main_thread.start()
	main_thread.join()
