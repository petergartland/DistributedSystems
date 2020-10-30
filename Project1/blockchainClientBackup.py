import socket
import select
import  errno
import threading
import time


HEADER_LENGTH = 10
IP = '127.0.0.1'
PORT = 50000
DELTA  =  5
RHO  =  .1
Tau  =  2

sim_time_at_sync  =  0
sys_time_at_sync  =  0
current_sim_time  =  0


def  current_sym_time(sim_time_at_sync, sys_time_at_sync):
	return  sim_time_at_sync  +  (time.time() - sys_time_at_sync)*(1  +  RHO)
	

my_username = input("Username: ")
client_socket  =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))

username  =  my_username.encode("utf-8")
username_header  =  f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
client_socket.send(username_header + username)



	

def getTransactions():
	while True:
		'''
		username_header = client_socket.recv(HEADER_LENGTH)
		if not len(username_header):
			print("connection closed by server")
			sys.exit()
		username_length = int(username_header.decode('utf-8'))
		username = client_socket.recv(username_length).decode('utf-8')
		'''
		message_header =  client_socket.recv(HEADER_LENGTH)
		if not len(message_header):
			print("connection closed by server")
			sys.exit()
		message_length  =  int(message_header.decode('utf-8'))
		message  =  client_socket.recv(message_length).decode('utf-8')
		timestamp_header  =  client_socket.recv(HEADER_LENGTH)
		timestamp_length  =  int(timestamp_header.decode('utf-8'))
		time = client_socket.recv(timestamp_length).decode('utf-8')
		print(f"{message} {time}")
			
def syncTime():
	pass
	
listenThread = threading.Thread(target=getTransactions)
timeThread = threading.Thread(target=syncTime)
listenThread.start()
timeThread.start()

while True:
	message = input()
	#if message == "time"
	#	print("inalid")
	if message is "balance":
		pass
		#scan blockchain
	else:
		message  =  message.encode('utf-8')
		message_header  =  f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
		current_time  =  str(time.time()).encode('utf-8')
		time_header = f"{len(current_time):<{HEADER_LENGTH}}".encode('utf-8') 
		client_socket.send(message_header + message + time_header + current_time) 
		''' 
	try:
		while True:
			username_header = client_socket.recv(HEADER_LENGTH)
			if not len(username_header):
				print("connection closed by server")
				sys.exit()
			username_length  =  int(username_header.decode('utf-8'))
			username  =  client_socket.recv(username_length).decode('utf-8')
			message_header  =  client_socket.recv(HEADER_LENGTH)
			message_length  =  int(message_header.decode('utf-8'))
			message  =  client_socket.recv(message_length).decode('utf-8')
			print(f"{username} > {message}")
			
	except  IOError as e:
		if	e.errno  !=  errno.EAGAIN  and  e.errno != errno.EWOULDBLOCK:
			print('Reading  error',  str(e))
			sys.exit()
		continue
		
	except	Exception  as  e:
		print('General error',  str(e))
		sys.exit()
		
'''
listenThread.join()
timeThread.join()

		
		
		
		
		
		
