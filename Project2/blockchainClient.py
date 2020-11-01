import socket
import select
import threading
import time
import random
import pickle


HEADER_LENGTH = 10  #each message starts with an interger = message length
IP = '127.0.0.1'  
PORT = 50000
DELTA = 1.0 #max difference between two clocks tolerated
RHO = .01 #drift speed of clock
TAU = .5 #max time to send message through network
BALANCE = 10 #starting balance of the clients


sim_time_at_sync = time.time() #keeps track of when the clock was last synced
sys_time_at_sync = time.time() #estimates the time when clock is synced
blockchain = [] #holds the blockchain transactions
blockchainBuffer = [] #temporarily holds transactions before they are moved to the blockchain
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
			#print(i, self.times[my_username][i], otherTT.times[otherUser][i])
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
			
			
def current_sim_time():
	return sim_time_at_sync + (time.time() - sys_time_at_sync)*(1 + RHO)
	


timeTable = TT()
#timeTable.newUser(my_username)


username = my_username.encode("utf-8")
username_header = f"{len(username):<{HEADER_LENGTH}}".encode("utf-8")
client_socket.send(username_header + username)


def getTransactions():
	'''
	receives incoming messages and finds the right function to handle the 			message. A thread will be passed this function.
	'''
	global timeTable
	global blockchain
	while True:
		message_header = client_socket.recv(HEADER_LENGTH)
		print('message header:', message_header)
		message_length = int(message_header.decode('utf-8'))
		#message = client_socket.recv(message_length).decode('utf-8')
		message = pickle.loads(client_socket.recv(message_length))
		timestamp_header = client_socket.recv(HEADER_LENGTH)
		timestamp_length = int(timestamp_header.decode('utf-8'))
		if str(message)[0] != '[':
			timestamp = client_socket.recv(timestamp_length).decode('utf-8')
		else:
			timestamp = client_socket.recv(timestamp_length)
			timestamp = pickle.loads(timestamp)
		if str(message)[0] == '<':
			updateBlockchainBuffer(message, timestamp)
		elif message[0:4] == 'time':
			#updateTime(message, timestamp)
			pass
		elif message[0:8] == 'new user':
			addUser(message)
		else:
			global logical_time
			print(f"{message} {timestamp}\n")
			print('')
			#sender = message[1:-1].split(sep=', ')[2]
			sender = message[2]
			#blockchainUpdate(message[1:-1].split(sep='[[')[1])
			blockchainUpdate(message[3])
			timeTable.updateTT(timestamp, sender)
			timeTable.printMe()
			logical_time = max(logical_time, timestamp.times[sender][sender])+1
			timeTable.incrementTT(logical_time)
			cleanBlockchain()


def cleanBlockchain():
	global blockchain
	global timeTable
	#print('here is block1:', blockchain)
	copy_blockchain = blockchain.copy()
	#print('here is block2:', blockchain)
	for i in copy_blockchain:
		remove = True
		for j in timeTable.times.keys():
			if timeTable.times[j][i[0]]	< i[3]:
				remove = False
				#print('here is i:',i, '\n')
				#print('here is block3:' blockchain)
		if remove:
			blockchain.remove(i)


def blockchainUpdate(block):
	global blockchain
	global balances
	global timeTable
	for i in block:
		if timeTable.times[my_username][i[0]] < i[3]:
			blockchain.append(i)
			balances[i[0]] -= i[2]
			balances[i[1]] += i[2]



def addUser(message):
	global timeTable
	new_user_name = message[10:]
	timeTable.newUser(new_user_name)
	timeTable.printMe()
	balances[new_user_name] = BALANCE


def updateBlockchainBuffer(message, timestamp):
	'''
	Stores a transfer into the local blockahin buffer. Called by recieve 			transaction function
	'''
	global blockchainBuffer
	transfer = message[1:-1].split(sep=', ')
	transfer[2] = int(transfer[2])
	transfer.append(float(timestamp))
	blockchainBuffer.append(transfer)
	print(f"{transfer[0]} sent ${transfer[2]} to {transfer[1]} at local time {transfer[3]}\n")


def updateTime(message, timestamp):
	'''
	Updates and prints the simulated time. time messages always start with 		'time', followed by the timestamp this client sent out its time request at, 	then lastly the timestamp from the time server (which is the timestamp 			dairable).
	'''
	global sys_time_at_sync
	global sim_time_at_sync
	print("previous time:", current_sim_time())
	sim_time_at_sync = float(timestamp) + (current_sim_time() - float(message[5:]))/2 #sets simulated time to be the time returned plus 1/2 of the round trip time
	sys_time_at_sync =  time.time()
	print("updated time: ", current_sim_time(),'\n')


def syncTime():
	'''
	Keeps track of when to send out a time request to keep the clock 				syncronized. A thread will be passed this function.
	'''
	global sys_time_at_sync
	while True:
		if time.time() - sys_time_at_sync > DELTA/(2*RHO):
			#print("updating time for: ", my_username)
			message = 'time'
			#sendMessageHelper(message)  @@@@@@@@@@@@@@@@@@@@@@@@@@@@
			time.sleep(DELTA/(2*RHO)-1)
			
			
'''
def getBalance():

#	Called when user askes for current balance. Calls updateBlockchain then checks to see how much money this account has.

	local_time = current_sim_time()  #records when function was called
	balance = BALANCE
	global blockchain
	print("Processing...\n")
	time.sleep(DELTA+2*TAU)
	updateBlockchain(local_time) #adds all transactions to the blockchain that occured before function call, i.e. before local_time
	#print("block chain:")
	for i  in  blockchain:
		#print(i)
		if i[0] == my_username:
			balance -= i[2]
		if i[1] == my_username:
			balance += i[2]
	return balance
'''

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
	
	
def updateBlockchain(local_time):
	'''
	places elements from blockchainBuffer that have a timestamp before 		"local_time"
	'''
	global blockchain
	global blockchainBuffer
	bufferCopy = blockchainBuffer.copy()
	bufferCopy.sort(key=returnTimestamp)
	#print("blockchain  Buffer:")
	for i in bufferCopy:
		#print(i)
		if i[3] < local_time:
			blockchain.append(i)
			blockchainBuffer.remove(i)
		else:
			print("")
			break
	print("")
	
	


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
	#timestamp  =  current_sim_time()
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
	#transfer.append(float(timestamp))
	transfer.append(logical_time)
	blockchain.append(transfer)
	balances[my_username] -=  transfer[2]
	balances[transfer[1]] += transfer[2]
	timeTable.incrementTT(logical_time)
	

def isValidMessage(message):
	return True


listenThread = threading.Thread(target=getTransactions)
timeThread = threading.Thread(target=syncTime)
listenThread.start()
timeThread.start()


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
			#message = message[:-1]
			#message += ', ' + my_username + ', [['
			#for i in timeTable.sendBlockchain(blockchain, message_list[0]):
			#	for j in i:
			#		message += str(j) + ', '
			#	message = message[:-2] + '], ['
			#message = message[:-3] + ']' #should only happen if we go through the loop atleast once
			sendMessageHelper(message)
			#sendMessageHelper(str(message_list))


listenThread.join()
timeThread.join()

