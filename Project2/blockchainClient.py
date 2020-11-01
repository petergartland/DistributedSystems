import socket
import select
import threading
import time
import random
import pickle


HEADER_LENGTH = 10  #each message starts with an interger = message length
IP = '127.0.0.1'  
PORT = 50000
TAU = .5 #max time to send message through network
BALANCE = 10 #starting balance of the clients



blockchain = [] #holds the blockchain transactions
balances  =  {}
logical_time = 0


my_username = input("Username: ")
balances[my_username] =  BALANCE
client_socket  =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))


class  TT:
	times = {}
	
	def newUser(self, user):
		if not  self.times:
			self.times = {user:{user:0}}
			
		times_copy  =  self.times.copy()
		for i in times_copy.keys():
			self.times[i][user] = 0
			
		self.times[user]  =  {}
		for  j  in  times_copy.keys():
			self.times[user][j]  =  0
			
		self.times[user][user]  =  0
	
				
	def updateTT(self, otherTT, otherUser):
		for i in self.times.keys():
			for j in self.times[i].keys():
				self.times[i][j] = max(self.times[i][j], otherTT.times[i][j])
		
		for i in self.times[my_username].keys():
			self.times[my_username][i] = max(self.times[my_username][i],  													otherTT.times[otherUser][i])
		

	def incrementTT(self, time):
		self.times[my_username][my_username]  =  time  
		
	
	def sendBlockchain(self, blockchain, receiver):
		blockchain_to_send = []
		for i in blockchain:
			if self.times[receiver][i[0]] < i[3]:
				blockchain_to_send.append(i)
		return blockchain_to_send
		
				
	def printMe(self):
		for  i  in  self.times.keys():
			row  =  i  +  ' knows '
			for  j  in  self.times[i].keys():
				row	+= j + ': ' + str(self.times[i][j]) + ' ' 
			print(row)
			
			


timeTable = TT()


username = my_username.encode("utf-8")
username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
client_socket.send(username_header + username)


def getTransactions():
	'''
	receives incoming messages and finds the right function to handle the 			message. A thread will be passed this function.
	'''
	global timeTable
	global blockchain
	global logical_time
	while True:
		#message_header = client_socket.recv(HEADER_LENGTH)
		message_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		message = pickle.loads(client_socket.recv(message_length))
		#timestamp_header = client_socket.recv(HEADER_LENGTH)
		timestamp_length= int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		timestamp = pickle.loads(client_socket.recv(timestamp_length))
		if message[0:8] == 'new user':
			addUser(message)
			
		else:
			print(f"{message} {timestamp}\n")
			print('')
			handleMessage(message, timestamp)
			

def addUser(message):
	global timeTable
	new_user_name = message[10:]
	timeTable.newUser(new_user_name)
	timeTable.printMe()
	balances[new_user_name] = BALANCE
	
	
def handleMessage(message, timestamp):
	global timeTable
	global logical_time
	sender = message[2]
	blockchainUpdate(message[3])
	timeTable.updateTT(timestamp, sender)
	timeTable.printMe()
	logical_time = max(logical_time, timestamp.times[sender][sender])+1
	timeTable.incrementTT(logical_time)
	cleanBlockchain()
	

def blockchainUpdate(block):
	global blockchain
	global timeTable
	global balances
	global timeTable
	for i in block:
		if timeTable.times[my_username][i[0]] < i[3]:
			blockchain.append(i)
			balances[i[0]] -= i[2]
			balances[i[1]] += i[2]


def cleanBlockchain():
	global blockchain
	global timeTable
	copy_blockchain = blockchain.copy()
	for i in copy_blockchain:
		remove = True
		for j in timeTable.times.keys():
			if timeTable.times[j][i[0]]	< i[3]:
				remove = False
		if remove:
			blockchain.remove(i)



def  getBalance():
	global balances
	for  i  in  balances.keys():
		print(i  +  ' has a balance of: ', balances[i])
	return balances[my_username]
	
	
def getBlockchain():
	print(blockchain)
	
	
def returnTimestamp(transaction):
	'''
	used for key in sort function.
	'''
	return transaction[3]
	
	
message_list = []			
def sendMessageHelper(message):
	'''
	Function makes thread then calls sendMessage function. Required to 	simulate network delay.
	'''
	t = threading.Thread(target=sendMessage, args=(message,))
	t.start()
	message_list.append(t)
	if len(message_list) > 5:
		message_list[0].join()
		del message_list[0]


def	sendMessage(message):
	'''
	Thread sleeps then sends message to server. Required to simulate network 		delay.
	'''
	#message  =  message.encode('utf-8')
	message_header  =  f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
	current_time  =  pickle.dumps(timeTable)
	time_header = f"{len(current_time):<{HEADER_LENGTH}}".encode('utf-8')
	time.sleep(random.uniform(0,TAU)) 
	client_socket.send(message_header + message + time_header + 			current_time) 
		

def isValid(message):
	if len(message) < 1 or not(message[0]  == '<' or message[0] == '['):
		response = "invalid request/format.\nTo get account balance enter  'balance', to send money enter a transaction in the form: <sender, receiver, amount>, to send a message to another user enter a command in the form: "
		print(response,'\n')
		return False
	elif  message[0]  ==  '<':
		return isValidTransaction(message)
	elif message[0] == '[':
		return isValidMessage(message)
		

def isValidTransaction(message):
	if message[0]  != '<' or message[-1] != '>' or	len(message[1:-1].split(sep=', ')) != 3:
		response = "invalid request/format.\nTo get account balance enter  'balance', to send money enter a transaction in the form: <sender, receiver, amount>, to send a message to another user enter a command in the form: "
		print(response,'\n')
		return False
		
	message_list = message[1:-1].split(sep = ', ')
	
	if message_list[0] != my_username:
		response = "you can only send money on behalf of yourself!"
		print(response, '\n')
		return False
	
	try:
		int(message_list[2])
	except:
		response  =  "you must send a dollar amount in the form of a positive iteger."
		print(response, '\n')
		return False
	
	if int(message_list[2]) <= 0:
		response  =  "you must send a dollar amount in the form of a positive iteger."
		print(response, '\n')
		return False
		
	balance = getBalance()
	if int(message_list[2])  >  balance:
		response  =  f"insufficient funds, current balance is {balance}"
		print(response, '\n') 
		return False
	global logical_time
	logical_time += 1
	storeTransaction(message)
	
	
def storeTransaction(transaction):
	global blockchain
	global balances
	global timeTable
	transfer = message[1:-1].split(sep=', ')
	transfer[2] = int(transfer[2])
	transfer.append(logical_time)
	blockchain.append(transfer)
	balances[my_username] -=  transfer[2]
	balances[transfer[1]] += transfer[2]
	timeTable.incrementTT(logical_time)
	

def isValidMessage(message):
	return True


listenThread = threading.Thread(target=getTransactions)
listenThread.start()


while True:
	message = input()
	if message == "balance":
		balance  =  getBalance()
		print("your balance is:", balance, '\n')
	elif message == "blockchain":
		getBlockchain()  
	elif message == "time":
		print(logical_time)
	elif message == "time table":
		timeTable.printMe()
	else:
		if isValid(message):  #makes sure the transaction/message is valid
			message_list = message[1:-1].split(sep=', ')
			message_list.append(my_username)
			message_list.append(timeTable.sendBlockchain(blockchain, 																message_list[0]))
			message = pickle.dumps(message_list)
			sendMessageHelper(message)

listenThread.join()

