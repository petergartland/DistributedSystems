import socket
import select
import random
import time
import threading
import pickle

HEADER_LENGTH = 10 #each message starts with an interger = message length
IP = '127.0.0.1'
PORT = 50000
TAU  =  2 #max time to send message through network

print("Server is  live")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((IP,	PORT))
server_socket.listen()

sockets_list = [server_socket] #list of the server socket and client sockets 												connected to server
usernames = [] #list of the usernames of clients connected to server
clients = {} # has the client sockets conected to the server as a key and the 						associated value is the username provided by the client.
username_to_socket  =  {}


def getUser(client_socket, client_address):
	'''
	gets and prints info from socket that has just made a connection with the 		server socket.
	'''
	global sockets_list
	global clients
	global usernames
	global username_to_socket
	try:
		message_header = client_socket.recv(HEADER_LENGTH)
		if not len(message_header):
			return False
			
		message_length = int(message_header.decode('utf-8'))
		user = client_socket.recv(message_length)
		sockets_list.append(client_socket)
		clients[client_socket] = {"header" : message_header, "data" : user}
		username_to_socket[user.decode('utf-8')]  =  client_socket
		
		usernames.append(user.decode('utf-8'))
		print(f"Accepted new connection from {client_address[0]} {client_address[1]} username: {user.decode('utf-8')}")
		sendUsers(client_socket)
	except:
		print("error getting user")


def sendUsers(client_socket):
	'''
sends info of all currently connected processes to the newly connected user and sends the info of the newly connected process to the other processes
	'''
	print('\nsending users\n')
	for i in usernames:
		message = 'new user: ' + i
		sendMessageHelper(message, '0', [client_socket])
	for i in sockets_list:
		if i != server_socket and i != client_socket:
			sendMessageHelper('new user: ' + usernames[-1], '0', [i])


def receive_message(client_socket):
	'''
	receives incoming messages and finds the right function to handle the 			message. A thread will be passesed this function.
	'''
	message_header = client_socket.recv(HEADER_LENGTH)
	print('message header received:', message_header)
	if not len(message_header):
		removeUser(client_socket)
		return "pass"
		
	message_length = int(message_header.decode('utf-8'))
	message	= client_socket.recv(message_length)
	timestamp_header = client_socket.recv(HEADER_LENGTH)
	timestamp_length = int(timestamp_header.decode('utf-8'))
	timestamp = client_socket.recv(timestamp_length)
	print('message received:', pickle.loads(message))
	if str(pickle.loads(message))[0]=='[':
		handleMessage(message, timestamp)
		return "pass"
		
	else:
		message_length = int(message_header.decode('utf-8'))
		return  {"header" : message_header, "data" : message, "time_header" : timestamp_header, "time" : timestamp}


def handleMessage(message, timestamp):
	contents = pickle.loads(message)
	print('contents', contents)
	t = threading.Thread(target=sendMessageForTT, args=(message, timestamp,  												[username_to_socket[contents[0]]]))
	t.start()
	message_list.append(t)
	if len(message_list) > 5:
		message_list[0].join()
		del message_list[0]


def sendMessageForTT(message, timestamp, clt_sockets): #this needs a helper function
	'''
	Thread sleeps then sends message to server. Required to simulate network 		delay.
	'''
	message_header  =  f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
	print('message header sent:', message_header)
	timestamp_header  =  f"{len(timestamp):<{HEADER_LENGTH}}".encode('utf-8')
	time.sleep(random.uniform(0,TAU))  
	for sock in clt_sockets:
		sock.send(message_header + message + timestamp_header + timestamp) 



message_list = []
def sendMessageHelper(message, timestamp, clt_sockets):
	'''
	Function makes thread then calls sendMessage function. Required to 	simulate network delay.
	'''
	t = threading.Thread(target=sendMessage, args=(message, timestamp, 																	clt_sockets))
	t.start()
	message_list.append(t)
	if len(message_list) > 5:
		message_list[0].join()
		del message_list[0]



def	sendMessage(message, timestamp, clt_sockets):
	'''
	Thread sleeps then sends message to server. Required to simulate network 		delay.
	'''
	message  =  pickle.dumps(message)
	message_header  =  f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
	timestamp  =  pickle.dumps(timestamp)
	timestamp_header  =  f"{len(timestamp):<{HEADER_LENGTH}}".encode('utf-8')
	time.sleep(random.uniform(0,TAU))  
	for sock in clt_sockets:
		sock.send(message_header + message + timestamp_header + timestamp) 
		

def removeUser(notified_socket):
	'''
	removes user from data structures when user disconnects
	'''
	print(f"Closed connection from {clients[notified_socket]['data'].decode('utf-8')}")
	sockets_list.remove(notified_socket)
	usernames.remove(clients[notified_socket]["data"].decode('utf-8'))
	del username_to_socket[clients[notified_socket]["data"].decode('utf-8')]
	del clients[notified_socket]
	

while True:
	read_sockets, _, __ = select.select(sockets_list, [], sockets_list)
	for notified_socket in read_sockets:
		if notified_socket == server_socket:
			client_socket, client_address = server_socket.accept()
			getUser(client_socket, client_address)
		else:
			message = receive_message(notified_socket)
			if message == "pass": #time request or invalid transaction
				continue
				
			else: #if message != 'pass' then message is a valid transaction
				user = clients[notified_socket]
				print(f"Received message from {user['data'].decode('utf-8')}: {message['data'].decode('utf-8')}")
				sendMessageHelper(message["data"].decode('utf-8'), 										message["time"].decode('utf-8'), clients)


		
			







