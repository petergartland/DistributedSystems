import socket
import select

HEADER_LENGTH = 10
IP = '127.0.0.1'
PORT = 50000

print("Server is  live")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((IP,	PORT))
server_socket.listen()

sockets_list = [server_socket]
clients = {}
usernames = []


def isValidMessage(client_socket, message):
	if len(message) < 1 or message[0]  != '<' or message[-1] != '>' or len(message[1:-1].split(sep=', ')) != 3:
		response = "invalid request/format.\nTo get account balance enter  'balance', to send money enter a transaction in the form: <sender, receiver, amount>"
		message_header  =  f"{len(response):<{HEADER_LENGTH}}".encode('utf-8')
		timestamp_header  =  f"{0:<{HEADER_LENGTH}}".encode('utf-8')
		client_socket.send(message_header +  response.encode('utf-8') + 
				timestamp_header)
		return False
		
	message_list = message[1:-1].split(sep = ', ')
	
	if message_list[0] != clients[client_socket]["data"].decode('utf-8'):
		response  =  "you can only send money on behalf of yourself!"
		message_header  =  f"{len(response):<{HEADER_LENGTH}}".encode('utf-8')
		timestamp_header  =  f"{0:<{HEADER_LENGTH}}".encode('utf-8')
		client_socket.send(message_header +  response.encode('utf-8')  +  					timestamp_header)
		return False
	
	if message_list[1] not in usernames:
		response  =  f"{message_list[1]} is an unknown user."
		message_header  =  f"{len(response):<{HEADER_LENGTH}}".encode('utf-8')
		timestamp_header  =  f"{0:<{HEADER_LENGTH}}".encode('utf-8')
		client_socket.send(message_header +  response.encode('utf-8')  +  					timestamp_header)
		return False

	try:
		int(message_list[2])
	except:
		response  =  "you must send a dollar amount in the form of an iteger."
		message_header  =  f"{len(response):<{HEADER_LENGTH}}".encode('utf-8')
		timestamp_header  =  f"{0:<{HEADER_LENGTH}}".encode('utf-8')
		client_socket.send(message_header +  response.encode('utf-8')  +  					timestamp_header)
		return False
				
	return True

def getUser(client_socket):
	try:
		message_header = client_socket.recv(HEADER_LENGTH)
		if not len(message_header):
			return False
		message_length = int(message_header.decode('utf-8'))
		return  {"header" : message_header, "data" : 											client_socket.recv(message_length)}	
	except:
		return False
		
		
def receive_message(client_socket):
	#try:
		message_header = client_socket.recv(HEADER_LENGTH)
		if not len(message_header):
			return False
		message_length =  int(message_header.decode('utf-8'))
		message	=  client_socket.recv(message_length)
		#get timestamp here  add  timestamp_header  +  timestamp  to  return
		timestamp_header  =  client_socket.recv(HEADER_LENGTH)
		timestamp_length  =  int(timestamp_header.decode('utf-8'))
		timestamp  =  client_socket.recv(timestamp_length)
		if not isValidMessage(client_socket, message.decode('utf-8')):
			return 'fuck'
		#add  timestamp_header  +  timestamp  to  return  dictionary
		message_length = int(message_header.decode('utf-8'))
		return  {"header" : message_header, "data" : message, "time_header" :
				timestamp_header, "time" : timestamp}	
	#except:
		return False
		
		
while True:
	read_sockets, _, exception_sockets = select.select(sockets_list, [], 
												sockets_list)
	for notified_socket in read_sockets:
		if notified_socket == server_socket:
			client_socket, client_address = server_socket.accept()
			user = getUser(client_socket)
			if user is False:
				print("error  user  name")
				continue
			
			sockets_list.append(client_socket)
			
			clients[client_socket] = user
			usernames.append(user["data"].decode('utf-8'))
			print(f"Accepted new connection from {client_address[0]}:{client_address[1]} username:{user['data'].decode('utf-8')}")
		
		else:
			message = receive_message(notified_socket)
			#print(message)
			if message  ==  "fuck":
				continue
			elif message is False:
				print(f"Closed connection from {clients[notified_socket]['data'].decode('utf-8')}")
				sockets_list.remove(notified_socket)
				usernames.remove(clients[notified_socket]["data"].decode('utf-8'))
				del clients[notified_socket]
				continue
				
			user = clients[notified_socket]
			print(f"Received message from {user['data'].decode('utf-8')}: {message['data'].decode('utf-8')}")
			
			for client_socket in clients:
				if client_socket != notified_socket:
					client_socket.send(message["header"] + message["data"] + message["time_header"] + message["time"])
		
	for notified_socket in exception_sockets:
		pass
		socket_list.remove(notified_socket)
		del client[notified_socket]
				
		
			







