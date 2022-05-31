# author: Jake Smith
# SID: 915986358
# Citations:
# (1) stackabuse.com - "Guide to Parsing HTML with BeautifulSoup in Python", https://stackabuse.com/guide-to-parsing-html-with-beautifulsoup-in-python/
# (2) Computer Networking - James Kurose; Keith Ross (152A textbook)

from socket import *
import os
from bs4 import BeautifulSoup
import time
from statistics import mean, pstdev
from numpy import random


recalc_count = 0
EstRTT = 0
DevRTT = 0

def create_socket():
	try:
		clientSocket = socket(AF_INET, SOCK_STREAM)
	except Exception as e:
		print("Socket creation error:", e)
		print("Retrying socket creation...")
		create_socket()
	return clientSocket

def connect(clientSocket, serverName, serverPort):
	try:
		clientSocket.connect((serverName, serverPort))
	except Exception as e:
		print("TCP connection error:", e)
		print("Retrying TCP handshake...")
		connect(clientSocket, serverName, serverPort)

def request_html(clientSocket, htmlRequest):
	try:
		clientSocket.send(htmlRequest.encode())
	except Exception as e:
		print("GET .html request error:", e)
		quit()

def request_img(clientSocket, img_http_request):
	try:
		clientSocket.send(img_http_request.encode())
	except Exception as e:
		print("GET .img request error:", e)
		print("Retyring .img request...")
		request_img(clientSocket, img_http_request)

def get_html_response(clientSocket, timeout):
	# ---- AboveTheFold Page Load Time justification ----
			# Per the assignment guidelines, our .recv buffer must be 4096 bytes
			# so the smallest amount of data that can be received is 4096 bytes.
			# When only 4096 bytes are received, only the AboveTheFold text and the image
			# http://webmit.edu/torrabla/www/alllndoors.jpg (and
			# a small amount more of text are received) so the time to receive 4096 bytes
			# plus the time to receive the 1 jpg is a good estimate of AboveTheFold Page Load Time.

	clientSocket.setblocking(0)
	sleep_time = timeout
	response = ''
	timeout_count = 0
	bytes_received = 0
	time1 = time.time()
	while True:
		time2 = time.time()
		if ((time2 - time1) > 1 * timeout) and response:
			break
		try:
			received = clientSocket.recv(4096)
			if received:
				if bytes_received < 4096:
					atf_time = time.time() - time1
				response += received.decode()
				timeout_count = 0
				sleep_time = timeout / 2
				bytes_received += 4096
				time1 = time.time()
			else:
				#print("Timeout triggered, sleeping for", sleep_time, "seconds...")
				time.sleep(sleep_time)
				sleep_time = (timeout / 2) * 2**(timeout_count) + random.uniform(0, 1)
				timeout_count += 1
		except Exception as e:
			pass
	return (response, time2, atf_time)

def get_img_response(clientSocket, timeout):
	clientSocket.setblocking(0)
	response = []
	timeout_count = 0
	sleep_time = timeout / 2
	time1 = time.time()
	while True:
		time2 = time.time()
		if ((time2 - time1) > 1 * timeout) and response:
			break
		try:
			received = clientSocket.recv(4096)
			if received:
				response.append(received)
				timeout_count = 0
				sleep_time = timeout / 2
				time1 = time.time()
			else:
				#print("Timeout triggered, sleeping for", sleep_time, "seconds...")
				time.sleep(sleep_time)
				sleep_time = (timeout / 2) * 2**(timeout_count) + random.uniform(0, 1)
				timeout_count += 1
		except Exception as e:
			pass
	final_response = b''.join(response)
	return (final_response, time2)

def parse_response(html_response, fp):
	try:
		# Citation (1) stackabuse.com
		if os.path.exists(fp):
			os.remove(fp)
		f = open(fp,'w')
		f.write(html_response)
		f.close()

		with open(fp) as fp:
			soup = BeautifulSoup(fp, "html.parser")

		img_list = soup.find_all("img")
		return img_list
	except Exception as e:
		print("html parsing error:", e)
		quit()


def parse_img(img_response, fp):
	header_len = img_response.find(b'\r\n\r\n')
	#print("Response Header:", img_response[:header_len].decode())

	img = img_response[header_len + 4:]
	try:
		# Citation: (1) stackabuse.com
		if os.path.exists(fp):
			os.remove(fp)
		f = open(fp,'wb')
		f.write(img)
		f.close()

	except Exception as e:
		print("img parsing error:", e)
		quit()

def make_img_req(src):
	request = "GET /"
	request += src
	request += " HTTP/1.1\r\n"
	request += "Host: 173.230.149.18\r\n"
	request += "Connection: close\r\n"
	request += "Content-type: image/jpeg\r\n"
	request += "X-Client-project: project-152A-part2\r\n\r\n"
	return request

def make_http_img_request(path, hostname):
	request = "GET "
	request += path
	request += " HTTP/1.1\r\n"
	request += "Host: "
	request += hostname
	request += "\r\n"
	request += "Connection: close\r\n"
	request += "X-Client-project: project-152A-part2\r\n\r\n"

	return request

def adjust_fp(input):
	length = len(input)
	i = length - 1
	while i >= 0:
		if input[i] == '/':
			break
		i -= 1
	output = input[i:]
	output = "ecs152a_imgs" + output
	return output

# Citation (2): Computer Networking - James Kurose; Keith Ross
def recalculate_timeout(RTT_list, sample_RTT):
	global recalc_count, EstRTT, DevRTT

	if recalc_count == 0:
		EstRTT = sample_RTT
	elif recalc_count == 1:
		EstRTT = (1 - .125) * mean(RTT_list) + (.125 * sample_RTT)
		DevRTT = (abs(RTT_list[1] - abs(RTT_list[0]))) / 2
	else:
		EstRTT = (1 - .125) * EstRTT + (.125 * sample_RTT)
		DevRTT = (1 - .25) * DevRTT + (.25 * abs(sample_RTT - EstRTT))

	recalc_count += 1
	return EstRTT + 3 * DevRTT



if __name__ == '__main__':
	serverName = '173.230.149.18'
	serverPort = 23662
	request_delays = []

	print("************************************************")
	print("HTTP Client Version: Non-Persistent HTTP")

	# ****************** Connection: close ******************
	# for non-persistent TCP connection
	htmlRequest = "GET /ecs152a.html HTTP/1.1\r\nHost: 173.230.149.18\r\nConnection: close\r\nX-Client-project: project-152A-part2\r\n\r\n"

	RTT_list = []
	# ---- request ecs152.html ----
	clientSocket = create_socket()

	# ---- start Total Page Load Time timer ----
	pageload_t1 = RTT_t1 = time.time()
	connect(clientSocket, serverName, serverPort)
	RTT_t2 = time.time()
	timeout = RTT_t2 - RTT_t1
	RTT_list.append(timeout)

	request_html(clientSocket, htmlRequest)
	# ---- returns html response and end Total Page Load timer value ----
	html_response, pageload_t2, atf_time = get_html_response(clientSocket, 1)

	# ****************** Non-persistent TCP connection ******************
	clientSocket.close()
	# ****************** Non-persistent TCP connection ******************

	print("Client successfully received and downloaded ecs152a.html.\n")
	timeout = recalculate_timeout(RTT_list, timeout)

	request_delays.append(pageload_t2 - pageload_t1)

	# ---- parse ecs152.html ----
	img_list = parse_response(html_response, "ecs152a.html")
	print("Downloading referenced images...")

	dir = "ecs152a_imgs"
	if not os.path.exists("ecs152a_imgs"):
		os.mkdir("ecs152a_imgs")

	# ---- request and parse images ----
	successful_downloads = 0
	for img in img_list:
		if 'http://' not in img["src"]:
			fp = img['src']
			img_http_request = make_img_req(img['src'])

			fp = fp[7:]
			fp = "ecs152a_imgs/" + fp

			# ****************** non-persistent TCP connection ******************
			clientSocket = create_socket()
			#timeout = mean(RTT_list)
			t1 = time.time()
			connect(clientSocket, serverName, serverPort)
			timeout_t = time.time()

			img_response_bytes = 0
			while img_response_bytes == 0:
				request_img(clientSocket, img_http_request)
				img_response, img_request_time2 = get_img_response(clientSocket, timeout)

				parse_img(img_response, fp)
				try:
					img_response_bytes = os.path.getsize(fp)
					if img_response_bytes < 10:
						continue
				except Exception as e:
					print(e)

			request_delays.append(img_request_time2 - t1)
			RTT_list.append(timeout_t - t1)
			timeout = recalculate_timeout(RTT_list, timeout_t - t1)

			# ****************** Non-persistent TCP connection ******************
			clientSocket.close()
			# ****************** Non-persistent TCP connection ******************
			#print("Successfully downloaded", img['src'])

			successful_downloads += 1
		else:
			fp = img['src']
			host_len = fp.find('.edu')
			hostname = fp[7:host_len + 4]

			img_request = make_http_img_request(fp, hostname)

			fp = adjust_fp(fp)

			# ****************** non-persistent TCP connection ******************
			clientSocket = create_socket()
			img_request_time1 = RTT_t1 = time.time()
			connect(clientSocket, hostname, 80)
			RTT_t2 = time.time()

			img_response_bytes = 0
			img_request_time1 = time.time()
			while img_response_bytes == 0:
				request_html(clientSocket, img_request)
				img_response, img_request_time2 = get_img_response(clientSocket, RTT_t2 - RTT_t1 + .5)

				parse_img(img_response, fp)
				try:
					img_response_bytes = os.path.getsize(fp)
					if img_response_bytes < 10:
						continue
				except Exception as e:
					print(e)

			request_delays.append(img_request_time2 - img_request_time1)

			# finish ATF time
			if fp == "http://web.mit.edu/torralba/www/allIndoors.jpg":
				atf_time += (img_request_time2 - img_request_time1)

			# ****************** Non-persistent TCP connection ******************
			clientSocket.close()
			# ****************** Non-persistent TCP connection ******************
			#print("Successfully downloaded", img['src'])

			successful_downloads += 1
	print("\n************************************************")
	print("Successfully downloaded images:", successful_downloads)
	print("Total PLT:", sum(request_delays), "seconds.")
	print("Total ATF PLT:", atf_time, "seconds.")
	print("EWMA RTT / calculated timeout:", timeout, "seconds.")
	print("Average Request Delay:", mean(request_delays), "seconds.")
	print("Requests per Second (RPS):", len(request_delays) / sum(request_delays))
	print("************************************************")
