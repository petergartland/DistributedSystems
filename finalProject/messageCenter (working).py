import socket
import select
import random
import time
import threading
import pickle

HEADER_LENGTH = 10 #each message starts with an interger = message length
IP = '127.0.0.1'
PORT = 50000
TAU  =  .1 #max time to send message through network

print("Server is  live")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((IP,	PORT))
server_socket.listen()

sockets_list = [server_socket] #list of the server socket and client sockets 												connected to server
usernames = [] #list of the usernames of clients connected to server
clients = {} # has the client sockets conected to the server as a key and the 						associated value is the username provided by the client.
server_to_socket = {}
client_to_socket = {}
username_to_socket  =  {}



def getUser(client_socket, client_address):
	'''
	gets and prints info from socket that has just made a connection with the 		server socket.
	'''
	global sockets_list
	global clients
	global usernames
	global username_to_socket
	global client_to_socket
	try:
		message_header = client_socket.recv(HEADER_LENGTH)
		if not len(message_header):
			return False
			
		message_length = int(message_header.decode('utf-8'))
		user = client_socket.recv(message_length)
		sockets_list.append(client_socket)
		clients[client_socket] = {"header" : message_header, "data" : user}
		user = user.decode('utf-8')
		username_to_socket[user] = client_socket
		if user.split()[0] == 'server':
			server_to_socket[user] = client_socket
			newServer(user)
		else:
			client_to_socket[user] = client_socket
			newClient(user)
		usernames.append(user)
		print(f"Accepted new connection from {client_address[0]} {client_address[1]} username: {user}")
	except:
		print("error getting user")
		
		
def newServer(user):
	'''
	lets the new server know about other servers and clients and lets the other servers and clients know about the new logged in server
	'''
	mtype = 'new client'
	sender = 'message center'
	for i in client_to_socket.keys():
		message = i
		sendMessage(mtype, sender, message, 0, server_to_socket[user])
	mtype = 'new server'
	for i in server_to_socket.keys():
		if i != user:
			message = i
			sendMessage(mtype, sender, message, 0, server_to_socket[user])
	message = user
	for i in client_to_socket.keys():
		sendMessage(mtype, sender, message, 0, client_to_socket[i])
	for i in server_to_socket.keys():
		if i != user:
			sendMessage(mtype, sender, message, 0, server_to_socket[i]) 
		

def newClient(user):
	'''
	Lets new client know about the servers and lets the servers know about the logged in client
	'''
	mtype = 'new client'
	sender = 'message center'
	message = user
	for i in server_to_socket.keys():
		sendMessage(mtype, sender, message, 0, server_to_socket[i])
	mtype = 'new server'
	for i in server_to_socket.keys():
		message = i
		sendMessage(mtype, sender, message, 0, client_to_socket[user])


def sendMessage(mtype, sender, message, ID, receiver):
	'''
	sends a message to the receiver socket
	'''
	mtype = pickle.dumps(mtype)
	mtype_length = f"{len(mtype):<{HEADER_LENGTH}}".encode('utf-8')
	sender = pickle.dumps(sender)
	sender_length = f"{len(sender):<{HEADER_LENGTH}}".encode('utf-8')
	term = pickle.dumps('NULL')
	term_length = f"{len(term):<{HEADER_LENGTH}}".encode('utf-8')
	ID = pickle.dumps(ID)
	ID_length = f"{len(ID):<{HEADER_LENGTH}}".encode('utf-8')
	message = pickle.dumps(message)
	message_length = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
	receiver.send(mtype_length + mtype + sender_length + sender + term_length + term + ID_length + ID + message_length + message)


def receive_message(client_socket):
	'''
	receives incoming messages and finds the right function to handle the 			message. A thread will be passesed this function.
	'''
	receiver_length = client_socket.recv(HEADER_LENGTH)
	print('message header received:', receiver_length)
	if not len(receiver_length.decode('utf-8')):
		removeUser(client_socket)
	else:	
		receiver = 	pickle.loads(client_socket.recv(int(receiver_length.decode('utf-8'))))
		print('receiver:', receiver)
		mtype_length = client_socket.recv(HEADER_LENGTH)
		mtype = client_socket.recv(int(mtype_length.decode('utf-8')))
		print('mtype:', pickle.loads(mtype))
		sender_length = client_socket.recv(HEADER_LENGTH)
		sender = client_socket.recv(int(sender_length.decode('utf-8')))
		print('sender:', pickle.loads(sender))
		term_length = client_socket.recv(HEADER_LENGTH)
		term = client_socket.recv(int(term_length.decode('utf-8')))
		print('term:', pickle.loads(term))
		ID_length = client_socket.recv(HEADER_LENGTH)
		ID = client_socket.recv(int(ID_length.decode('utf-8')))
		print('ID:', pickle.loads(ID))
		message_length = client_socket.recv(HEADER_LENGTH)
		message = client_socket.recv(int(message_length.decode('utf-8')))
		print('message:', message, '\n')
		if receiver in usernames:
			username_to_socket[receiver].send(mtype_length + mtype + sender_length + sender + term_length + term + ID_length + ID + message_length + message) 
		
		

def removeUser(notified_socket):
	'''
	removes user from data structures when user disconnects
	'''
	print(f"Closed connection from {clients[notified_socket]['data'].decode('utf-8')}")
	sockets_list.remove(notified_socket)
	user = clients[notified_socket]["data"].decode('utf-8')
	usernames.remove(user)
	del username_to_socket[user]
	if user in client_to_socket:
		del client_to_socket[user]
	elif user in server_to_socket:
		del server_to_socket[user]
	del clients[notified_socket]
	
	

while True:
	read_sockets, _, __ = select.select(sockets_list, [], sockets_list)
	for notified_socket in read_sockets:
		if notified_socket == server_socket:
			client_socket, client_address = server_socket.accept()
			getUser(client_socket, client_address)
		else:
			receive_message(notified_socket)
