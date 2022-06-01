# README: This entire file was written by the instructors of ECS 152A, and was NOT written by Jake Smith. Jake Smith is NOT an author of this file,
# and this file is only included in Jake Smith's github in order to properly test TCP_Tahoe.py (which was authored by Jake Smith).
# Again, Jake Smith does not claim ownership over any part of this code.


# Importing the required libraries
import socket
import re


# Defining Global Parameters
# IP address of the receiver. "" implies localhost
IP_ADDRESS = ""
# Port number on localhost on which receiver runs
PORT = int(input("Enter the Port number you want your receiver to run: "))
# Size of the buffer, defining the maximum data that can be buffered for transmission at a time
BUFFER_SIZE = 1500
# Window size at the receiver (practically very large)
RWND = 1000000


# Instatiating a UDP Socket
receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Binding the Socket to specified IP address and Port
receiver_socket.bind((IP_ADDRESS, PORT))

# List maintaining sequence numbers that are received by the receiver
received_sequences = [0] * (RWND+1)
received_sequences[0] = 1

# Variable to maintain acknowledgement number of the received packets
acknowledgement_number = -1

# Receiver keeps running indefinitely to receive the data
while True:

	# Inititalising exception flag to handle the Sequence Number Exception.
	exception_flag = False

	# Receiving the packet from the sender
	packet_data, sender_address = receiver_socket.recvfrom(BUFFER_SIZE)

	# Extracting the sequence number
	try:
		seq = int(packet_data.decode().split("|")[0])
		if not(type(seq) is int):
			raise TypeError("Error: Sequence Number is not an Integer!")
		elif seq < 0:
			raise TypeError("Error: Sequence Number is not a Non-Negative Integer!")

		# If sequence number received is correct, generate the acknowledgement
		# Set current received sequence to 1
		received_sequences[seq] = 1

		for i in range(1, RWND+1):
			if received_sequences[i] == 0:
				acknowledgement_number = i-1
				break

	# Handling the Issue with Sequence Numbers
	except BaseException:

		exception_flag = True
		acknowledgement_number = -1
		print("Sequence Number Exception!")
	
	# Sends the acknowledgement to the sender
	finally:
	
		print("Sending Acknowledgement #", acknowledgement_number)
		receiver_socket.sendto(str(acknowledgement_number).encode(), sender_address)
	
