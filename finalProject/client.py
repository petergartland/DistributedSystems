import socket
import select
import threading
import time
import random
import pickle
import hashlib

#TODO: need to impliment timeouts resends and leader change resends using TID's

HEADER_LENGTH = 10  #each message starts with an interger = message length
IP = '127.0.0.1'  
PORT = 50000
TAU = 5 #max time to send message through network
BALANCE = 10 #starting balance of the clients
TIMEOUT = 20

TID = 1
TID_list = []
TID_to_transaction = {}
TID_to_times = {}
servers = []
leader = 'unknown'


my_username = input("Username: ")
my_username = "client " + my_username
#balances[my_username] =  BALANCE
client_socket  =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))

username = my_username.encode("utf-8")
username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
client_socket.send(username_header + username) #sends username to server to be broadcasted out to the other users.


def getTransactions():
	'''
	receives incoming messages and finds the right function to handle the 			message. A thread will be passed this function.
	'''
	global servers
	global leader
	global TID_list
	global TID_to_transaction
	global TID_to_times
	while True:
		mtype_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		mtype = pickle.loads(client_socket.recv(mtype_length))
		sender_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		sender = pickle.loads(client_socket.recv(sender_length))
		term_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		term = pickle.loads(client_socket.recv(term_length))
		ID_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		ID = pickle.loads(client_socket.recv(ID_length))
		message_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		message = pickle.loads(client_socket.recv(message_length))
		if ID in TID_list or ID == 0:
			if mtype == 'message' or mtype == 'error':
				print(message, 'from:', sender, '\n')
				if sender != 'message center' and sender != leader:
					leaderChange(sender)
			if mtype == 'server response':
				print(message, 'from:', sender, '\n')		
			if mtype == 'new server':
				servers.append(message)
				print("server:", message, "added")
		if ID in TID_list:
			TID_list.remove(ID)
			del TID_to_transaction[ID]
			del TID_to_times[ID]
			
			
def TIDTimeout():
	global TID_list
	global TID_to_transaction
	global TID_to_times
	while True:
		if len(TID_list) > 0:
			times_copy = TID_to_times.copy()
			for i in times_copy.keys():
				if times_copy[i] < time.time() - TIMEOUT:
					sendMessageHelper(TID_to_transaction[i], TID)
					TID_to_times[i] = time.time()
				else:
					time.sleep(.1)
		else:
			time.sleep(.1) 
		
		
def leaderChange(sender):
	global leader
	global TID_list
	global TID_to_transaction
	global TID_to_times
	leader = sender
	for i in TID_list:
		sendMessageHelper(TID_to_transaction[i], i)
		TID_to_times[i] = time.time()
		
				

message_list = []			
def sendMessageHelper(message, ID):
	'''
	Function makes thread then calls sendMessage function. Required to 	simulate network delay.
	'''
	global TID
	if ID == -1:
		TID += 1
		ID = TID
	t = threading.Thread(target=sendMessage, args=(message,ID,))
	t.start()
	if ID not in TID_list:
		TID_list.append(ID)
		TID_to_transaction[ID] = message
		TID_to_times[ID] = time.time()
	message_list.append(t)
	if len(message_list) > 5:
		message_list[0].join()
		del message_list[0]


def	sendMessage(message, ID):
	'''
	Thread sleeps then sends message to server. Required to simulate network 		delay.
	'''
	if leader == 'unknown':
		receiver = pickle.dumps(servers[0])
	else:
		receiver = pickle.dumps(leader)
	receiver_header = f"{len(receiver):<{HEADER_LENGTH}}".encode('utf-8')
	mtype = pickle.dumps('transaction')
	mtype_header = f"{len(mtype):<{HEADER_LENGTH}}".encode('utf-8')
	sender = pickle.dumps(my_username)
	sender_header = f"{len(sender):<{HEADER_LENGTH}}".encode('utf-8')
	term = pickle.dumps('NULL')
	term_header = f"{len(term):<{HEADER_LENGTH}}".encode('utf-8')
	ID = pickle.dumps(ID)
	ID_header = f"{len(ID):<{HEADER_LENGTH}}".encode('utf-8')
	message = pickle.dumps(message)
	message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
	time.sleep(random.uniform(0,TAU)) 
	client_socket.send(receiver_header + receiver + mtype_header + mtype + sender_header + sender + term_header + term + ID_header + ID + message_header + message)
	
	
	
listenThread = threading.Thread(target=getTransactions)
listenThread.start()

timeoutThread = threading.Thread(target=TIDTimeout)
timeoutThread.start()

while True:
	message = input()
	if message == 'TID':
		print(TID_list)
		print(TID_to_transaction)
		print(TID_to_times)
	elif message == 'state':
		print(my_username)
	else:
		sendMessageHelper(message, -1)

listenThread.join()
timeoutThread.start()
