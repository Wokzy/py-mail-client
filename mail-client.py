"""
Simple mail client based on SMTPlib and IMAPlib
SSL supported
Client is thread

Tested on greenmail/stanalone
"""

import ssl
import email
import smtplib
import imaplib
import threading

from config import SERVER_DOMAIN, SMTP_PORT, IMAP_PORT, \
					USE_SSL, LOGIN, PASSWORD, INBOX_FOLDER


__author__ = 'Yegor Yershov'

'''
class Message:
	def __init__(self, sender:str=None, reciever:str=None, content=None, date=None):
		"""
		Init settings
		"""
		self.sender = sender
		self.reciever = reciever
		self.content = content
		self.date = date


	def setup_from_fetch_responce(self, responce:tuple):
		"""
		Init settings from fetch responce
		"""
		pass
'''

class MailClient(threading.Thread):
	def __init__(self, logging=False):
		"""
		Initting super, settings setting
		"""
		super().__init__(daemon=True)

		self.logging = logging
		self.recieved_messages = []


	def smtp_authorize(self):
		"""
		SMTP authorization to server
		"""

		if USE_SSL:
			smtp = smtplib.SMTP_SSL(SERVER_DOMAIN, SMTP_PORT)
		else:
			smtp = smtplib.SMTP(SERVER_DOMAIN, SMTP_PORT)

		status = smtp.ehlo() # using ESMTP
		if status[0] != 250: # 250 means "everything is fine"
			raise RuntimeError(f'Server hello responce is {status[0]}: """{status[1].decode()}"""')

		#self.log(f'status: {status}')

		status = smtp.login(LOGIN, PASSWORD)
		if status[0] != 235: # 235 means login is successfull
			raise RuntimeError(f'Server login failed: {status[1]}')

		#self.log('login is successful')
		return smtp


	def imap_authorize(self):
		"""
		IMAP authorization to server
		"""

		if USE_SSL:
			imap = imaplib.IMAP4_SSL(host=SERVER_DOMAIN, port=IMAP_PORT)
		else:
			imap = imaplib.IMAP4(host=SERVER_DOMAIN, port=IMAP_PORT)

		status = imap.login(LOGIN, PASSWORD)
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
		email.message.Message.items() - return all message add. info (subject, date) (use get_payload() to get payload)
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


	def run(self):
		"""
		Thread function
		"""
		self.smtp_authorize()
		#self.send_message(reciever=input('Enter reciever -> '), message=input('Enter message -> '))
		inbox = self.load_inbox()
		for msg in inbox:
			print(f'"""{msg.get_payload()}"""', msg.items(), end='\n\n')


if __name__ == '__main__':
	main_thread = MailClient(logging=True)
	main_thread.start()
	main_thread.join()
