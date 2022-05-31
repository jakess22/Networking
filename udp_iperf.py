from socket import *
import time
import os
from numpy import random

if __name__ == '__main__':
	serverName = '173.230.149.18'
	serverPort = 5006

	timeout_secs = 10


	clientSocket = socket(AF_INET, SOCK_DGRAM)

	msg = 'ping'
	response = ''
	last_perc = 0
	bytes_received = 0
	timeout_secs = 10
	timeout_count = -1
	response = ''

	t1 = time.time()
	clientSocket.sendto(msg.encode(), (serverName, serverPort))
	clientSocket.settimeout(10)

	while bytes_received <= 1300000:
		try:
			rec = clientSocket.recv(4096)
			response += rec.decode()
			t2 = time.time()
			timeout_secs = 10
			timeout_count = -1
			bytes_received += 4096
			percent = int((bytes_received / 1300000) * 100)
			if percent != last_perc:
				print("Received %: ", percent)
				last_perc = percent
		except Exception as e:
			#print(e)
			print("Timeout triggered. Sleeping for", timeout_secs, "seconds...")
			time.sleep(timeout_secs) # sleep for timeout_secs
			timeout_count += 1
			timeout_secs = timeout_secs * 2**(timeout_count) + random.uniform(0, 1)
			if timeout_secs > 600:
				timeout_secs = 600
			print("Resending file request.")


	clientSocket.close()
	print("\nClient received file.")

	if os.path.exists("iperf_response.txt"):
  		os.remove("iperf_response.txt")
	f = open("iperf_response.txt", "a")
	f.write(response)
	f.close()

	f_size = bytes_received * 8 # bits
	print("File size:", f_size, "bits |", bytes_received, "bytes.")
	print("Time elapsed:", t2 - t1, "seconds.")
	print("Throughput:", f_size / (t2 - t1), "bps.")
