"""
Simple mail client based on SMTPlib
SSL supported
Client is thread
"""

# CONSTANTS
#==================
SERVER_DOMAIN = '127.0.0.1'
SERVER_PORT = 1025
USE_SSL = False
PASSWORD = ''
LOGIN = 'sender@example.com'
#==================


import ssl
import smtplib
import threading


__author__ = 'Yegor Yershov'


class MailClient(threading.Thread):
	def __init__(self, server_domain:str, server_port:int, login:str, 
					password:str, use_ssl:bool = True, logging=False):
		"""
		Initting super, settings setting
		"""
		super().__init__(daemon=True)

		self.use_ssl = use_ssl
		self.logging = logging

		self.login = login
		self.password = password

		self.server_port = server_port
		self.server_domain = server_domain


	def authorize_to_server(self):
		"""
		Server authorization
		"""
		self.server = smtplib.SMTP(self.server_domain, self.server_port)
		status = self.server.ehlo() # using ESMTP

		if status[0] != 250: # 250 means "everything is fine"
			raise RuntimeError(f'Server hello responce is {status[0]}: """{status[1].decode()}"""')

		self.log(f'status: {status}')

		if self.use_ssl:
			context = ssl.create_default_context()
			try:
				self.server.starttls(context=context)
			except smtplib.SMTPNotSupportedError:
				self.log('SSL is not supported by this server', priority=True)

		status = self.server.login(self.login, self.password)
		if status[0] != 235: # 235 means login is successfull
			raise RuntimeError(status[1].decode())

		self.log(f'login is successful')


	def log(self, message:str, priority:bool=False):
		"""
		Writes logs if they are turned on
		"""
		if self.logging or priority:
			print(f'[INFO] {message}')


	def send_message(self, reciever:str, message:str):
		self.server.sendmail(self.login, reciever, message)
		self.log(f'Message has been sent to {reciever}')


	def run(self):
		"""
		Thread function
		"""
		self.authorize_to_server()
		self.send_message(reciever=input('Enter reciever -> '), message=input('Enter message -> '))


if __name__ == '__main__':
	main_thread = MailClient(server_domain=SERVER_DOMAIN, server_port=SERVER_PORT,
							login=LOGIN, password=PASSWORD, use_ssl=USE_SSL, logging=True)
	main_thread.start()
	main_thread.join()
