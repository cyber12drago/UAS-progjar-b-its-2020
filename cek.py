import socket
import time
import sys
import asyncore
import logging
import subprocess
import os

def next_free_port( port=9000, max_port=40000 ):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while port <= max_port:
        try:
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            port += 1
    raise IOError('no free ports')

class BackendList:
	def __init__(self):
		self.servers=[]
		self.servers.append(('127.0.0.1', 9002))
		self.servers.append(('127.0.0.1', 9003))
		self.servers.append(('127.0.0.1', 9004))
		self.current=0

	def getlength(self):
		return len(self.servers)

	def addserver(self, portnumber):
		self.servers.append(('127.0.0.1',portnumber))

	def getserver(self):
		s = self.servers[self.current]
		self.current=self.current+1
		return s

class Backend(asyncore.dispatcher_with_send):
	def __init__(self,targetaddress):
		asyncore.dispatcher_with_send.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.connect(targetaddress)
		self.connection = self

	def handle_read(self):
		try:
			self.client_socket.send(self.recv(8192))
		except:
			pass
	def handle_close(self):
		try:
			self.close()
			self.client_socket.close()
		except:
			pass


class ProcessTheClient(asyncore.dispatcher):
	def handle_read(self):
		data = self.recv(8192)
		if data:
			self.backend.client_socket = self
			self.backend.send(data)
	def handle_close(self):
		self.close()

class Server(asyncore.dispatcher):
	def __init__(self,portnumber):
		asyncore.dispatcher.__init__(self)
		self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_reuse_addr()
		self.bind(('',portnumber))
		self.listen(5)
		self.bservers = BackendList()
		logging.warning("load balancer running on port {}" . format(portnumber))

	def handle_accept(self):
		pair = self.accept()
		if pair is not None:
			sock, addr = pair
			logging.warning("connection from {}" . format(repr(addr)))

			#menentukan ke server mana request akan diteruskan
			currentserver = self.bservers.current
			if(currentserver >= self.bservers.getlength()):
				newport = next_free_port()
				subprocess.Popen(['python','async_server.py',str(newport)],preexec_fn=os.setsid)
				s = socket.socket()
				i = 1
				while (i <=3):
					try:
						time.sleep(0.05)
						s.connect((addr,newport))
						i= 4
					except Exception as e:
						i += 1
					finally:
						s.close()
				self.bservers.addserver(newport)
			bs = self.bservers.getserver()
			logging.warning("koneksi dari {} diteruskan ke {}" . format(addr, bs))
			backend = Backend(bs)


			#mendapatkan handler dan socket dari client
			handler = ProcessTheClient(sock)
			handler.backend = backend


def main():
	portnumber=44444
	try:
		portnumber=int(sys.argv[1])
	except:
		pass
	svr = Server(portnumber)
	asyncore.loop()

if __name__=="__main__":
	main()


