import socket
import select
import errno
import threading
import time
import random


HEADER_LENGTH = 10
IP = '127.0.0.1'
PORT = 50000
DELTA  =  15.0
RHO  =  .25
TAU  =  .25

#random.seed()
#SIGN  =  random.randrange(2)

#if SIGN ==  1:
#	RHO  =  -RHO

sim_time_at_sync  =  time.time()
sys_time_at_sync  =  time.time()


def  current_sim_time():
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
		timestamp = client_socket.recv(timestamp_length).decode('utf-8')
		if message[0:4] == 'time':
			updateTime(message, timestamp)
		#elif message[0]  ==  '<':
		#	updateBlockchainBuffer(message, timestamp)
		else:
			print(f"{message} {timestamp}")

def updateTime(message, timestamp):
	global sys_time_at_sync
	global sim_time_at_sync
	print("previous time:", current_sim_time())
	sim_time_at_sync = float(timestamp) + (current_sim_time() - float(message[5:]))/2
	sys_time_at_sync =  time.time()
	print("updated time: ", current_sim_time(),'\n')


def updateBlockchainBuffer(message, timestamp):
	pass
	
	
def syncTime():
	global sys_time_at_sync
	while True:
		if time.time() - sys_time_at_sync > DELTA/(2*RHO):
			print("updating  time for: ",  my_username)
			message = 'time'
			sendMessageHelper(message)
			time.sleep(TAU*4)
			

message_list  =  []			
def sendMessageHelper(message):
	t  =  threading.Thread(target=sendMessage, args=(message,))
	t.start()
	message_list.append(t)
	if len(message_list) > 5:
		message_list[0].join()
		del message_list[0]
		
def	sendMessage(message):
	message  =  message.encode('utf-8')
	message_header  =  f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
	current_time  =  str(current_sim_time()).encode('utf-8')
	time_header = f"{len(current_time):<{HEADER_LENGTH}}".encode('utf-8')
	time.sleep(random.uniform(0,TAU)) 
	client_socket.send(message_header + message + time_header + current_time) 
			
time_updated  =  False	
listenThread = threading.Thread(target=getTransactions)
timeThread = threading.Thread(target=syncTime)
listenThread.start()
timeThread.start()

while True:
	message = input()
	if message is "balance":
		pass
		#scan blockchain
	else:
		sendMessageHelper(message)
	

listenThread.join()
timeThread.join()

		
		
		
		
		
		
