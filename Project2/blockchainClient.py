import socket
import select
import threading
import time
import random
import pickle


HEADER_LENGTH = 10  #each message starts with an interger = message length
IP = '127.0.0.1'  
PORT = 50000
TAU = 2 #max time to send message through network
BALANCE = 10 #starting balance of the clients


blockchain = [] #holds the blockchain transactions
balances  =  {} #keys are user names, value is that users balance
logical_time = 0


my_username = input("Username: ")
balances[my_username] =  BALANCE
client_socket  =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))


class  TT:
	'''
	this class stores a Wuu Bernstein time table modeled as a dictionary with 	keys corresponding to the other users of the system and the values contain what this client knows the key knows about the other users. The values themselves are dictionaires. Has methods to update the table.
	'''
	times = {} #the Wuu Bernstein table
	
	def newUser(self, user): 
		'''
		adds a row and column (with time = 0) in the timetable for a new user
		'''
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
		'''
		updates table when given another time table and the user that sent that 		time table.
		'''
		for i in self.times.keys():
			for j in self.times[i].keys():
				self.times[i][j] = max(self.times[i][j], otherTT.times[i][j])
		
		for i in self.times[my_username].keys():
			self.times[my_username][i] = max(self.times[my_username][i],  													otherTT.times[otherUser][i])
		

	def incrementTT(self, time):
		'''
		increases what the timetable says that this process knows about itself
		'''
	
		self.times[my_username][my_username]  =  time  
		
	
	def sendBlockchain(self, blockchain, receiver):
		'''
		Determines what elements of the blockchain need to be added when 			sending a message to receiver
		'''
		blockchain_to_send = []
		for i in blockchain:
			if self.times[receiver][i[0]] < i[3]:
				blockchain_to_send.append(i)
		return blockchain_to_send
		
				
	def printMe(self):
		'''
		prints out the timetable
		'''
		print(f"printing time table for {my_username}\n") 
		for  i  in  self.times.keys():
			row  =  i  +  ' knows '
			for  j  in  self.times[i].keys():
				row	+= j + ': ' + str(self.times[i][j]) + ' ' 
			print(row)
		print('')


timeTable = TT()


username = my_username.encode("utf-8")
username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
client_socket.send(username_header + username) #sends username to server to be broadcasted out to the other users.


def getTransactions():
	'''
	receives incoming messages and finds the right function to handle the 			message. A thread will be passed this function.
	'''
	global timeTable
	global blockchain
	global logical_time
	while True:
		message_length = int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		message = pickle.loads(client_socket.recv(message_length))
		timestamp_length= int(client_socket.recv(HEADER_LENGTH).decode('utf-8'))
		timestamp = pickle.loads(client_socket.recv(timestamp_length))
		if message[0:8] == 'new user':#server is telling process about new user
			addUser(message)
			
		else:
			printMessage(message, timestamp)
			#print(f"{message} {timestamp}\n")
			print('')
			handleMessage(message, timestamp)
			

def addUser(message):
	'''
	calls the timetables method to update itself to add the new user
	'''
	global timeTable
	new_user_name = message[10:]
	timeTable.newUser(new_user_name)
	timeTable.printMe()
	balances[new_user_name] = BALANCE


def printMessage(message, timestamp):
	if type(message) == list:
		print(f"{message[2]} sends the message: {message[1]}", '\n')
		
	else:
		print(f"{message} {timestamp}\n")
	
	
def handleMessage(message, timestamp):
	'''
calls blockchainUpdate to get data from the blockchain that the sending process sent. Calls TT's method to update itself given the timetable from the process that sent the message. Then calls cleanBlockchain to garbage collect on blockchain. 
	'''
	global timeTable
	global logical_time
	sender = message[2]
	blockchainUpdate(message[3])
	timeTable.updateTT(timestamp, sender)
	logical_time = max(logical_time, timestamp.times[sender][sender])+1
	timeTable.incrementTT(logical_time)
	cleanBlockchain()
	

def blockchainUpdate(block):
	'''
	adds new blockchain elements that we contained in a received message.
	'''
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
	'''
	garbage collects. If timetable shows that all process know about an event then that even is removed from blockchain
	'''
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
	'''
	prints out everybodies balance and returns your balance.
	'''
	global balances
	for  i  in  balances.keys():
		print(i  +  ' has a balance of: ', balances[i])
	print('')
	return balances[my_username]
		

def isValid(message):
	'''
	first check if an input message/transaction is in valid format. If so sends transactions or message to appropraite function to be handled.
	'''
	if len(message.split(sep=', ')) < 2 or not(message[0]  == '<' or message[0] == '['):
		response = "invalid request/format.\nTo get account balance enter  'balance', to send money enter a transaction in the form: <sender, receiver, amount>, to send a message to another user enter a command in the form:	[receiver, message] "
		print(response,'\n')
		return
		
	elif  message[0]  ==  '<':
		isValidTransaction(message)
		
	elif message[0] == '[':
		isValidMessage(message)
	
	return

def isValidTransaction(message):
	'''
	checks if input message is a valid transaction. If so it then updates its blockchain and balances
	'''
	global logical_time
	message_list = message[1:-1].split(sep = ', ')
	if message[0]  != '<' or message[-1] != '>' or len(message_list) != 3:
		response = "invalid request/format.\nTo get account balance enter  'balance', to send money enter a transaction in the form: <sender, receiver, amount>"
		print(response,'\n')
		return
	
	if message_list[0] != my_username:
		response = "you can only send money on behalf of yourself!"
		print(response, '\n')
		return
	
	if message_list[1] not in balances:
		response = f"{message_list[1]} is an unknown user."
		print(response, '\n')
		return
		
	try:
		int(message_list[2])
	except:
		response = "you must send a dollar amount in the form of a positive iteger."
		print(response, '\n')
		return
	
	if int(message_list[2]) <= 0:
		response = "you must send a dollar amount in the form of a positive iteger."
		print(response, '\n')
		return
		
	if balances[my_username]  <  int(message_list[2]):
		response = f"insufficient funds, current balance is {balances[my_username]}"
		print(response, '\n') 
		return

	logical_time += 1
	timeTable.incrementTT(logical_time)
	storeTransaction(message)


def isValidMessage(message):
	global logical_time
	'''
	checks if input message is in valid format. If so it passes message to sendMessageHelper to send the message
	'''
	message_list = message[1:-1].split(sep=', ')
	if len(message_list) != 2 or message[0] != '[' or message[-1] != ']':
		response = "invalid request/format.\nTo get account balance enter  'balance', to send a message enter a message in the format: [receiver, message]"
		print(response, '\n')
		return
		
	if message_list[0] not in balances:
		response = f"{message_list[0]} is an unknown user."
		print(response, '\n') 
		return
	
	logical_time += 1
	timeTable.incrementTT(logical_time)
	message_list.append(my_username)
	message_list.append(timeTable.sendBlockchain(blockchain, message_list[0]))
	message = pickle.dumps(message_list)
	sendMessageHelper(message)


def storeTransaction(transaction):
	'''
	given an input transaction it updates its blockchain and balances to reflect the transaction
	'''
	global blockchain
	global balances
	global timeTable
	global logical_time
	transfer = message[1:-1].split(sep=', ')
	transfer[2] = int(transfer[2])
	transfer.append(logical_time)
	blockchain.append(transfer)
	balances[my_username] -=  transfer[2]
	balances[transfer[1]] += transfer[2]


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
	message_header  =  f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
	current_time  =  pickle.dumps(timeTable)
	time_header = f"{len(current_time):<{HEADER_LENGTH}}".encode('utf-8')
	time.sleep(random.uniform(0,TAU)) 
	client_socket.send(message_header + message + time_header + current_time) 
	
	
listenThread = threading.Thread(target=getTransactions)
listenThread.start()


while True:
	message = input()
	if message == "balance":
		getBalance()
		
	elif message == "blockchain":
		print(blockchain, '\n')
		
	elif message == "time":
		print(logical_time, '\n')
		
	elif message == "time table":
		timeTable.printMe()
		
	else:
		isValid(message)

listenThread.join()

