import socket
import select
import threading
import time
import random
import pickle
import hashlib
import string


HEADER_LENGTH = 10  #each message starts with an interger = message length
IP = '127.0.0.1'  
PORT = 50000
TAU = 2 #max time to send message through network
BALANCE = 100 #starting balance of the clients


blockchain = [] #holds the blockchain transactions
balances = {}
estimated_balances = {}
servers = []
leader = 'unknown'
state = 'follower'
current_term = 0
voted_for = 'NULL'
HEARTBEAT = 20
THRESHOLD = 50
time_at_last_heartbeat_received = 0
time_at_last_heartbeat_sent = 0
BACKOFF = 15



my_username = input("Username: ")
my_username = "server " + my_username
client_socket  =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))

username = my_username.encode("utf-8")
username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
client_socket.send(username_header + username) #sends username to message center to be broadcasted out to the other users.


def	election():
	global current_term
	global time_at_last_heartbeat_received
	global time_at_last_heartbeat_sent
	global voted_for
	global state
	while True:
		if len(servers) == 2 and time.time() - time_at_last_heartbeat_received > THRESHOLD:
			time.sleep(random.uniform(0,BACKOFF))
			if time.time() - time_at_last_heartbeat_received > THRESHOLD: 
				time_at_last_heartbeat_received = time.time()
				time_at_last_heartbeat_sent = time.time()
				current_term += 1
				voted_for = my_username
				state = 'candidate'
				for i in servers:
					if len(blockchain) == 0:
						sendMessageHelper(i, 'vote request', my_username, [0,0])	
					else:
						sendMessageHelper(i, 'vote request', my_username, [blockchain[-1].term, len(blockchain)])
		else:
			time.sleep(.1)
			
			
def sendHeartbeat():
	global time_at_last_heartbeat_sent
	global time_at_last_heartbeat_received
	global state
	while True:
		if time.time() - time_at_last_heartbeat_sent > HEARTBEAT and state == 'leader':
			time_at_last_heartbeat_sent = time.time()
			time_at_last_heartbeat_received = time.time()
			print("sending heartbeat\n")
			for i in servers:
				sendMessageHelper(i, 'heartbeat', my_username, 'leader sending heartbeat')
			time.sleep(HEARTBEAT)
		else:
			time.sleep(.1)
	

def getRandomString(length):
	letters = string.ascii_lowercase
	result_str = ''.join(random.choice(letters) for i in range(length))
	return result_str


class blockchainNode():
	global current_term
	def __init__(self, node, transaction):
		self.term = current_term
		if node == 'NULL':
			self.phash = 'NULL'
		else:
			to_hash = str(node.block[0]) + str(node.block[1]) + str(node.block[2]) + node.nonce
			self.phash = hashlib.sha256(to_hash.encode('utf-8')).hexdigest()
		self.nonce = 'NULL'
		self.block = ['NULL', 'NULL', 'NULL']
		self.block[0] = transaction
		
	def addBlock(self, command):
		if self.block[0] == 'NULL':
			self.block[0] = command
			return False
		elif self.block[1] == 'NULL':
			self.block[1] = command
			return False
		else:
			self.block[2] = command
			return True
	
	def findNonce(self):
		blocks = str(self.block[0]) + str(self.block[1]) + str(self.block[2])
		random_str = getRandomString(10)
		print("finding nonce \n")
		if hashlib.sha256(random_str.encode('utf-8')).hexdigest()[0] <= '2':
			self.nonce = random_str
			print("nonce found \n")
			return True
		return False
		


def getTransactions():
	'''
	receives incoming messages and finds the right function to handle the 			message. A thread will be passed this function.
	'''
	global blockchain
	global logical_time
	global current_term
	global voted_for
	global state
	global leader
	global time_at_last_heartbeat_received
	while True:
		mtype_length= int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		mtype = pickle.loads(client_socket.recv(mtype_length))
		print("mtype:", mtype)
		sender_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		sender = pickle.loads(client_socket.recv(sender_length))
		print("sender:", sender)
		term_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		term = pickle.loads(client_socket.recv(term_length))
		print("term:", term)
		message_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		message = pickle.loads(client_socket.recv(message_length))
		print("message:", message, '\n')
		if term == 'NULL':
			term = current_term
		if term >= current_term:
			if term > current_term:
				current_term = term
				voted_for = 'NULL'
				state = 'follower'
				#should we change leader here?
			if mtype == 'message':
				print(message, '\n')
			if mtype == 'transaction':
				print(message, leader, '\n')
				if leader != my_username:
					if leader == 'unknown':
						sendMessageHelper(servers[0], mtype, sender, message)
					else:
						sendMessageHelper(leader, mtype, sender, message)
				else:
					handleTransaction(message, sender)
			if mtype == 'new client':
				addUser(message)
			if mtype == 'new server':
				servers.append(message)
				print("server:", message, "added\n")
				print('servers:', servers)
			if mtype == 'vote request':
				print('vote request from:', sender, '\n')
				handleVoteRequest(message, sender)
			if mtype == 'vote':
				print("I am the leader!\n")
				leader = my_username
				state = 'leader'
			if mtype == 'heartbeat':
				leader = sender
				time_at_last_heartbeat_received = time.time()
				
			
def handleVoteRequest(message, sender):
	global blockchain
	global time_at_last_heartbeat_received
	global voted_for
	global leader
	if voted_for == 'NULL' or voted_for == sender:
		if len(blockchain) == 0:
			time_at_last_heartbeat_received = time.time()
			print("i am voting for", sender)
			sendMessageHelper(sender, 'vote', my_username, 'you got my vote')
			voted_for = sender
			leader = sender
		elif blockchain[-1].term < message[0] or (blockchain[-1].term == message[0] and len(blockchain) <= message[1]):
			time_at_last_heartbeat_received = time.time()
			sendMessageHelper(sender, 'vote', my_username, 'you got my vote')
			print("i am voting for", sender)
			voted_for = sender
			leader = sender

def handleTransaction(message, sender):
	'''
	inserts an incoming transaction into the appropriate block
	'''
	global blockchain
	if message == "balance":
		message = [sender] 
	else:
		message = isValidMessage(message, sender)
	if message:
		if len(message) > 1:
			estimated_balances[message[0]] -= message[2]
			estimated_balances[message[1]] += message[2]
		if len(blockchain) == 0:
			blockchain.append(blockchainNode('NULL', message))
		elif blockchain[-1].nonce == 'NULL' and blockchain[-1].block[2] == 'NULL':
			blockchain[-1].addBlock(message)
		else:
			blockchain.append(blockchainNode(blockchain[-1], message))
		


def isValidMessage(message, sender):
	'''
	checks if message is in the valid format. If not it rejects the transaction and sends a reponse to the sending client
	'''
	if len(message) == 0 or message[0] != '<' or message[-1] != '>':
		response = 'invalid format. type "balance" to check you balance or <sender, receiver, amount> to make a transaction'
		sendMessageHelper(sender, 'server response', my_username, response)
		return False
	message = message[1:-1].split(sep=', ')
	if len(message) != 3:
		response = 'invalid format. type "balance" to check you balance or <sender, receiver, amount> to make a transaction'
		sendMessageHelper(sender, 'server response', my_username, response)	
		return False
	elif message[0] != sender:
		print("isvalidmessage sender:", sender)
		print("isvalidmessage [0]:", message[0])
		response = 'you can only send money on behalf of yourself'
		sendMessageHelper(sender, 'server response', my_username, response)
		return False
	elif message[1] not in balances:
		response = f'{message[1]} is an unknown user' 
		sendMessageHelper(sender, 'server response', my_username, response)
		return False
	try:
		message[2] = int(message[2])
	except:
		response = 'The amount of money you send must be an a number'
		sendMessageHelper(sender, 'server response', my_username, response)
		return False
	if message[2] > estimated_balances[sender]:
		response = "you dont have enough money to complete this transaciton"
		sendMessageHelper(sender, 'server response', my_username, response)
		return False
	return message
		

def addUser(user):
	'''
	adds the new client to the list of balances
	'''
	balances[user] = BALANCE
	estimated_balances[user] = BALANCE
	print("user:", user, "added\n")

#next must add some checking to make sure we are not overspending. update balances when block is commited and 

def getNonce():
	'''
	A thread is passed this function to work on finding the nonce of the for the next block in the blockchain. It will also notify clients once their transaction has been commited  
	'''
	global blockchain
	i = 0
	while True:
		if len(blockchain) > i:
			if blockchain[i].findNonce():
				print('block i:', blockchain[i].block)
				updateAndNotify(i) #This should be moved to after block commitment once raft is implimented
				i += 1
			time.sleep(.5)
		else:
			time.sleep(.1)
			
			
			
def updateAndNotify(i):
	'''
	called once block i is commited. It lets the clients know that their transaction has been completed
	'''
	for j in blockchain[i].block:
		print("this is j:", j)
		if len(j) == 1:
			print("here")
			sendMessageHelper(j[0], 'server response', my_username, 'your balance is: ' + str(balances[j[0]])) 
		elif j != 'NULL':
			print('block j:', j)
			balances[j[0]] -= int(j[2])
			balances[j[1]] += int(j[2])
			sendMessageHelper(j[0], 'server response', my_username, 'you have successfully sent ' + j[1] + ' $' + str(j[2]))
			
			
message_list = []			
def sendMessageHelper(receiver, mtype, sender, message):
	'''
	Function makes thread then calls sendMessage function. Required to 	simulate network delay.
	'''
	t = threading.Thread(target=sendMessage, args=(receiver, mtype, sender, message,))
	t.start()
	message_list.append(t)
	if len(message_list) > 5:
		message_list[0].join()
		del message_list[0]


def printBlockchain():
	'''
	prints conteds of the blockchain
	'''
	global blockchain
	print("printing blockchain \n")
	for i in blockchain:
		print('term:', i.term)
		print('phash:', i.phash)
		print('nonce:', i.nonce)
		print('transaction 1:', i.block[0])
		print('transaction 2:', i.block[1])
		print('transaction 3:', i.block[2])


def	sendMessage(receiver, mtype, sender, message):
	'''
	Thread sleeps then sends message to server. Required to simulate network 		delay.
	'''
	global current_term
	receiver = pickle.dumps(receiver)
	receiver_header = f"{len(receiver):<{HEADER_LENGTH}}".encode('utf-8')
	mtype = pickle.dumps(mtype)
	mtype_header = f"{len(mtype):<{HEADER_LENGTH}}".encode('utf-8')
	sender = pickle.dumps(sender)
	sender_header = f"{len(sender):<{HEADER_LENGTH}}".encode('utf-8')
	term = pickle.dumps(current_term)
	term_header = f"{len(term):<{HEADER_LENGTH}}".encode('utf-8')
	message = pickle.dumps(message)
	message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
	time.sleep(random.uniform(0,TAU)) 
	print('sender:', sender, 'sending:', message, '\n')
	client_socket.send(receiver_header + receiver + mtype_header + mtype + sender_header + sender + term_header + term + message_header + message)
	
	
electionThread = threading.Thread(target=election)
electionThread.start()	
	
listenThread = threading.Thread(target=getTransactions)
listenThread.start()
	
nonceThread = threading.Thread(target=getNonce)
nonceThread.start()


heartbeatThread = threading.Thread(target=sendHeartbeat)
heartbeatThread.start()


while True:
	message = input()
	if message == 'print':
		printBlockchain()
	else:
		#sendMessageHelper(message)
		pass
		

listenThread.join()
nonceThread.join()
electionThread.join()
heartbeatThread.join()
