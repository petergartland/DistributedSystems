import os

print(os.getcwd())

x = '/home/peter/DistributedSystems/finalProject/'

y = x + 'block.txt'

try:
	with open(y, 'r') as f:
		print('opened')
except:
	with open(y, 'x') as f:
		print('created')
		
with open (y, 'w') as f:
	f.write('hello\n')
	f.write('world')

with open(y, 'r') as f:
	print(f.readline())
