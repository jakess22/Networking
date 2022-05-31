from socket import *
import time
from numpy import random

serverName = '173.230.149.18'
serverPort = 12000

timeout_secs = 10


if __name__ == '__main__':
	clientSocket = socket(AF_INET, SOCK_DGRAM)

	msg = 'ping'
	response = 'null'

	response_list = []
	RTT_list = []
	timeout_secs = 10
	timeout_count = -1
	i = 0
	while i < 10:
		t1 = time.time()
		print("Current time:", t1, "| Message number: ", i + 1)

		clientSocket.sendto(msg.encode(), (serverName, serverPort))
		clientSocket.settimeout(10)
		try:
			response = clientSocket.recv(1024)
			t2 = time.time()
			timeout_count = -1
			RTT = t2 - t1
			# Question: is this enough to handle missing packets
			if response.decode() == 'PING':
				print("Client received message:", response.decode())
				print("Round Trip Time for ping #", i + 1, ":", RTT, "seconds\n")
				response_list.append(response.decode())
				RTT_list.append(RTT)
				timeout_secs = 10
				i += 1
		except socket.timeout:
			print("Timeout triggered. Sleeping for", timeout_secs, "seconds...")
			time.sleep(timeout_secs) # sleep for timeout_secs
			timeout_count += 1
			timeout_secs = timeout_secs * 2**(timeout_count) + random.uniform(0, 1)
			if timeout_secs >= 600:
				i += 1
				continue # if timeout_secs >= 10 mins, packet is lost (do not append to response_lsit)


	clientSocket.close()

	print("\nTotal number of success packets is", len(response_list))
	print("Total number of packets lost is", 10 - len(response_list))

	print("Successful packet RTTs (seconds) are ")
	for i in range(len(RTT_list)):
		print(RTT_list[i])
	print("Minimum RTT:", min(RTT_list), "seconds")
	print("Maximum RTT:", max(RTT_list), "seconds")
	print("Average RTT:", sum(RTT_list) / len(RTT_list), "seconds")
	print("Sum of", len(RTT_list), "RTTs:", sum(RTT_list), "seconds")
