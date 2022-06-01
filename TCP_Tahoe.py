# TCP - Dynamic Sliding Window
# author: Jake Smith
# SID: 915986358
# Citations:
# (1) Computer Networking - James Kurose; Keith Ross (152A textbook)

# ***** README ***** :
# Dynamic Timeout vs. Dynamic Blocking Timeout vs. delay calculation

# This implementation uses nonblocking sockets open for dynamically calculated durations (the blocking timeout) to minimize delay.

# Dynamic Timeout: Calculated using textbook dynamic timeout, only used for checking each timeout per packets sent. Not related to delay calculations.

# Dynamic Blocking Timeout: calculated using modified textbook dynamic timeout calculations. Not related to delay calculations

# Per packet delay is calculated after receive() function call, as long as a timeout did not occur. All new packets acknowledged will have their corresponding delays calculated at once.


import socket
from socket import AF_INET, SOCK_DGRAM
import time
import os
from statistics import mean
from math import log
import matplotlib.pyplot as plt

seq_num = 1
start_seq_num = 1
window_size = 1
ssthresh = 16
ack_num = 0
max_ack = 0
last_ack = 0
duplicate_ack_count = 0

senderIP = ""
senderPort = 0
blocking_timeout = .5
timeout = 1
total_timeouts = 0

response = ''
est_RTT = 0
dev_RTT = 0

RTT_history = []
window_size_history = [1]
last_packet_in_window = 1
all_window_packets_received = True


timeout_t1 = 0
timeout_flag = False
timeout_count = 0

total_packets = 0
start_loc = 0
end_loc = start_loc + 1000

delay_t1_list = []
delay_t2_list = []


last_t1 = 0
last_t2 = 0

packet_size_list = []


have_packets_to_send = True
packets_created = 0
packets_sent = 0

window_packets = []


def send(senderSocket):
	global senderIP, senderPort, window_size, window_packets, packets_sent, timeout_t1, delay_t1_list, last_t1, seq_num, all_window_packets_received, timeout_flag
	i = seq_num
	j = 0
	t1 = 0
	last_t1 = time.time()

	# The window_packets are dynamically added depending on how much available room there is in the 		# window, based on how many packets have been ACKed. This requires a minimum here in case there 		# are less actual window_packets than the window size.
	while i < len(window_packets) + seq_num:
		# do not send packets that have already been sent in the window
		if i > packets_sent:
			# delay_t1 = start delay timer for this packet
			# last_t1 = used as RTT estimate for timeout calculation
			delay_t1 = last_t1 = time.time()
			senderSocket.sendto(window_packets[j].encode(), (senderIP, senderPort))
			packets_sent += 1
			print("Sequence Number of Packet Sent:", seq_num + j)
			delay_t1_list.append(delay_t1)

		i += 1
		j += 1
	if all_window_packets_received:
		# if all packet windows are received, we want to restart our timer for this round of packets sent.
		timeout_t1 = last_t1
		all_window_packets_received = False
		# README: We assume that all packets are sent "instantaneously". I use a delay_t1_list 			to simplify later per packet
		# delay calculations (this also gives a slightly more accurate time for when the packet 			is sent).
		# I use only 1 variable for the timer for simplicity of calculating timeouts. Since we 			assumed
		# all packets are sent at once, this logic works.


# retransmit timed out packet
def resend(senderSocket, packet_number):
	global senderIP, senderPort, window_size, window_packets, packets_sent, timeout_t1, seq_num, last_t1

	if len(window_packets) > 0:
		timeout_t1 = last_t1 = time.time()
		senderSocket.sendto(window_packets[packet_number].encode(), (senderIP, senderPort))
		print("\nRetransmit --> Number of Packet Sent:", seq_num)
	else:
		print("resend() error: no packets in window to send")

# quick retransmit of triple ACKed packet
def triple_ack_quick_resend(senderSocket, packet_index_to_send):
	global senderIP, senderPort, window_size, window_packets, packets_sent, timeout_t1, seq_num, last_t1

	if len(window_packets) > 0:
		timeout_t1 = last_t1 = time.time()
		senderSocket.sendto(window_packets[packet_index_to_send].encode(), (senderIP, senderPort))
		print("\nRetransmit --> Number of Packet Sent:", seq_num)
	else:
		print("triple_ack_quick_resend() error: no packets in window to send")


# Citation: (1) Computer Networking - James Kurose; Keith Ross (152A textbook)
def calculate_RTT():
	global blocking_timeout, last_t1, last_t2, est_RTT, dev_RTT, RTT_history, timeout, timeout_flag

	# only use nontimed out delays for blocking timeout calculation
	if not timeout_flag:
		sample_RTT = last_t2 - last_t1

		est_RTT = (.875 * est_RTT) + (.125 * sample_RTT)
		dev_RTT = (.75 * dev_RTT) + .75 * (abs(sample_RTT - est_RTT))
		blocking_timeout = est_RTT + 5 * dev_RTT
		timeout = est_RTT + 4 * dev_RTT
		RTT_history.append(blocking_timeout * 1000)



def receive(senderSocket):
	global seq_num, window_size, start_seq_num, have_packets_to_send, window_packets, timeout_t1, response, last_t2, max_ack, blocking_timeout, ssthresh, delay_t2_list, window_size_history, last_packet_in_window, all_window_packets_received, total_packets, duplicate_ack_count, timeout_flag, timeout_count, last_ack, ack_num, total_timeouts

	senderSocket.setblocking(0)

	response = ''
	last_t2_check = True # used for RTT calculation only, not delay calculation
	t1 = time.time()
	while True:
		if (time.time() - t1) > blocking_timeout:
			break
		try:
			response, receiver_address = senderSocket.recvfrom(2048)
			delay_t2 = time.time()
			if response and last_t2_check: # used for RTT calculation only, not delay calculation
				last_t2 = delay_t2
				last_t2_check = False
			if response:
				timeout_count = 0
				resend_flag = False
				ack_num = int(response.decode().split("|")[0])

				print("\nSender Sequence Number:", seq_num)
				print("     --> ACK Number Received:", ack_num)

				# these continues are put in for efficiency of handling large number of incoming packets
				if ack_num < last_ack:
					continue
				if ack_num < seq_num:
					continue
				if ack_num < max_ack:
					continue

				if ack_num == seq_num:
					delay_t2_list.append(delay_t2)

					seq_num += 1
					end_of_window = seq_num + window_size - 1
					print("     --> New sender seq:", seq_num)

					if ack_num > max_ack:
						max_ack = ack_num

					have_packets_to_send = True
					duplicate_ack_count = 0
					timeout_flag = False

				elif ack_num > seq_num:
					i = seq_num
					while i <= ack_num: # cumultive ACKs, so add this delay_t2 for packets up to this ACK
						delay_t2_list.append(delay_t2)
						i += 1

					seq_num = ack_num + 1

					print("     --> New sender seq:", seq_num)
					if ack_num > max_ack:
						max_ack = ack_num

					have_packets_to_send = True
					duplicate_ack_count = 0
					timeout_flag = False

				if ack_num == last_ack:
					print("Duplicate ACK received")
					duplicate_ack_count += 1

					if duplicate_ack_count == 3:
						final_timeouts += 1
						print("3 duplicate ACKs received. Shrinking window size to 1 and resending packet", ack_num - (last_packet_in_window - window_size) + 1)

						# if 3 duplicate ACKs, shrink window size to 1
						window_size = 1

						window_size_history.append(window_size)
						if len(window_packets) > 0:
							triple_ack_quick_resend(senderSocket, ack_num - (last_packet_in_window - window_size) + 1)
						duplicate_ack_count = 0
					#have_packets_to_send = True
					timeout_flag = False
				if ack_num == last_packet_in_window:
					all_window_packets_received = True

					# all packets in window have been ACKed, so we can clear it and make new packets to be sent
					window_packets.clear()

				# adjust window size - if less than ssthresh, increase by 1 per ACK
				if window_size < ssthresh:
					window_size += 1
					window_size_history.append(window_size)
					end_of_window = seq_num + window_size - 1

				last_ack = ack_num

				print("\nReceive -- Current cwnd:", window_size)
				print("Current Window: [", end =" ")
				i = seq_num
				while i < seq_num + window_size:
					print(i, end =" ")
					i += 1
				print("]")

		except Exception as e:
			pass


def check_timeout(senderSocket):
	global window_packets, timeout_t1, seq_num, window_size_history, window_size, timeout, blocking_timeout, timeout_flag, timeout_count, ack_num
	if (time.time() - timeout_t1) >= timeout:
		if len(window_packets) > 0: # no need to time out if there are no packets

			timeout_count += 1
			adjusted_timeout = timeout * timeout_count
			print("TIMEOUT: Packet number", seq_num, "timeout. Sleeping for", adjusted_timeout, "seconds.")
			time.sleep(adjusted_timeout)


			print("Shrinking window size to 1.")
			print("Doubling timeout value.")

			window_size = 1
			window_size_history.append(window_size)
			print("Resending packet", seq_num)
			print("\nCurrent cwnd:", window_size)
			print("Current Window: [", end =" ")
			i = seq_num
			while i < seq_num + window_size:
				print(i, end =" ")
				i += 1
			print("]")

			timeout_flag = True
	else:
		timeout_flag = False


def make_packets():
	global total_packets, seq_num, window_size, start_loc, end_loc, window_packets, packets_created, packet_size_list, delay_t1_list, last_packet_in_window, all_window_packets_received
	if (total_packets - seq_num) < window_size:
		window_size = total_packets - seq_num + 1
	print("\nSend -- Current cwnd:", window_size)
	print("Current Window: [", end =" ")
	i = seq_num
	while i < seq_num + window_size:
		print(i, end =" ")
		i += 1
	print("]")

	if all_window_packets_received:
		last_packet_in_window = seq_num + window_size - 1


	i = seq_num
	while i < seq_num + window_size:
		if i > packets_created:
			payload = data[start_loc:end_loc]
			packet = str(i) + "|" + payload
			window_packets.append(packet)
			packet_size_list.append(len(packet)) # bytes

			start_loc += 1000
			end_loc += 1000
			packets_created += 1
		i += 1




if __name__ == '__main__':
	senderPort = int(input("Enter Port number in use by receive.py: "))

	with open("message.txt", "r") as f:
		data = f.read()

	senderSocket = socket.socket(AF_INET, SOCK_DGRAM)

	total_packets = int(len(data) / 1000) + 1

	sample_RTT_list = []
	tp_list = []
	final_delay_list = []

	first_call = True
	seq_count = 0
	timeout_flag = False

	# Timer for entire process. Not related to delay calculation.
	t1 = time.time()
	# Iterate until all packets are sent and ACKed.
	while seq_num <= total_packets:
		start_seq_buff = seq_num # to store what seq_num this iteration starts on
		if timeout_flag:
			# find timed out packet in window_packets to resend
			i = 0
			while i < len(window_packets):
				packet_number = int(window_packets[i].split("|")[0])
				if packet_number == seq_num:
					break
				i += 1
			if i == len(window_packets):
				i -= 1
			# resend the timed out packet
			resend(senderSocket, i)

		if (not timeout_flag) and have_packets_to_send:
			make_packets()
			send(senderSocket)
			have_packets_to_send = False

		receive(senderSocket)

		# if all packets are received (and none further have been sent yet), there are no packets to check for timeouts
		if (not all_window_packets_received) and len(window_packets) > 0:
			check_timeout(senderSocket)
			if timeout_flag:
				total_timeouts += 1
				continue # skip any delay calculation

		# if window > ssthresh, increase only once per RTT (i.e. once per receive call when something is received)
		if response and window_size >= ssthresh:
			window_size += 1
			end_of_window = seq_num + window_size - 1
			window_size_history.append(window_size)
		# est_RTT has not yet been calculated, so this first RTT is a good estimate for it
		if first_call:
			est_RTT = last_t2 - last_t1
			first_call = False
		# only calculate RTT if no timeout

		if not timeout_flag:
			# used for timeout calculation, not delay calculation
			sample_RTT_list.append(abs(last_t2 - last_t1))

			# calculate timeout and blocking timeout
			calculate_RTT()
		# only calculate delay if all window packets are ACKed so all delays are accounted for
		if not timeout_flag and all_window_packets_received:
			# calculate per packet delay
			# delay_t1_list and delay_t2_list hold individual packet delay values
			# these are added to final delay list of all packet delays
			i = 0
			while i < min(len(delay_t2_list), len(delay_t1_list)):
				final_delay_list.append(delay_t2_list[i] - delay_t1_list[i])
				i += 1
			delay_t2_len = len(delay_t2_list)
			i = 0
			while i < delay_t2_len:
				if len(delay_t1_list) > 0:
					delay_t1_list.pop(0)
				if len(delay_t2_list) > 0:
					delay_t2_list.pop(0)
				i += 1
			#if len(final_delay_list) > 0:
			#	print("Current mean delay:", mean(final_delay_list))

			# calculate per packet throughput
			i = start_seq_buff
			if len(packet_size_list) > 0 and len(final_delay_list) > 0:
				while i < seq_num:
					if i < len(final_delay_list):
						tp_list.append((packet_size_list[0] * 8) / final_delay_list[i - 1])
						packet_size_list.pop(0)
					i += 1
			#if len(tp_list) > 0:
			#	print("Current TP", mean(tp_list))

	# end process time, not related to delay calculation
	t2 = time.time()
	print("Total process time:", t2 - t1, "seconds.")
	#print("Total timeouts:", total_timeouts)
	# calculate average per packet delay
	mean_delay = mean(final_delay_list)
	print("Average delay:", mean_delay * 1000, "milliseconds.") # ms

	# calculate average per packet throughput
	mean_tp = mean(tp_list)
	print("Average throughput:", mean_tp, "bits per second.")
	print("Performance =", log(mean_tp) - log(mean_delay * 1000))
	#plt.plot(final_delay_list)
	#plt.show()
	#plt.plot(tp_list)
	#plt.show()
	#plt.plot(window_size_history)
	#plt.show()
