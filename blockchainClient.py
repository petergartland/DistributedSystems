import socket
import select
import errno
import threading
import time
import random


HEADER_LENGTH = 10
IP = '127.0.0.1'
PORT = 50001
DELTA  =  1.0
RHO  =  .01
TAU  =  .25
BALANCE  =  100

#random.seed()
#SIGN  =  random.randrange(2)

#if SIGN ==  1:
#	RHO  =  -RHO

sim_time_at_sync  =  time.time()
sys_time_at_sync  =  time.time()
blockchain  =  []
blockchainBuffer  =  []


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
		elif message[0]  ==  '<':
			updateBlockchainBuffer(message, timestamp)
		else:
			print(f"{message} {timestamp}\n")
			




def updateTime(message, timestamp):
	global sys_time_at_sync
	global sim_time_at_sync
	print("previous time:", current_sim_time())
	sim_time_at_sync = float(timestamp) + (current_sim_time() - float(message[5:]))/2
	sys_time_at_sync =  time.time()
	print("updated time: ", current_sim_time(),'\n')



def updateBlockchainBuffer(message, timestamp):
	global blockchainBuffer
	transfer = message[1:-1].split(sep=', ')
	transfer[2]  =  int(transfer[2])
	transfer.append(float(timestamp))
	blockchainBuffer.append(transfer)
	#if transfer[0] != my_username:
	print(f"{transfer[0]} sent ${transfer[2]} to {transfer[1]} at local time {transfer[3]}\n")
	

def returnTimestamp(transaction):
	return transaction[3]
	
def updateBlockchain(local_time):
	global blockchain
	global blockchainBuffer
	bufferCopy = blockchainBuffer.copy()
	bufferCopy.sort(key=returnTimestamp)
	print("blockchain  Buffer:")
	for i in bufferCopy:
		print(i)
		if i[3] < local_time:
			blockchain.append(i)
			blockchainBuffer.remove(i)
		else:
			print("")
			break
	print("")
def getBalance():
	balance  =  BALANCE
	global blockchain
	print("Processing...\n")
	local_time   =  current_sim_time()
	time.sleep(DELTA+2*TAU)
	updateBlockchain(local_time)
	print("block chain:")
	for i  in  blockchain:
		print(i)
		if i[0] == my_username:
			balance -= i[2]
		if i[1] == my_username:
			balance += i[2]
	print("your balance is:", balance, '\n')
 	



def syncTime():
	global sys_time_at_sync
	while True:
		if time.time() - sys_time_at_sync > DELTA/(2*RHO):
			print("updating  time for: ",  my_username)
			message = 'time'
			sendMessageHelper(message)
			time.sleep(DELTA/(2*RHO)-1)
			#think  of  something  go  for  previous  line!!!
			

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
	if message == "balance":
		getBalance()
	else:
		if isValid(message):
			sendMessageHelper(message)
	

listenThread.join()
timeThread.join()

		
		
		
		
		
		
