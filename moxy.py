#!/usr/bin/env python

__author__ = "Neil Loknath"
__copyright__ = "Copyright 2013, Neil Loknath"
__license__ = "BSD"
__version__ = "0.1"
__maintainer__ = "Neil Loknath"
__email__ = "nloko@nloko.ca"
__status__ = "Alpha"

import urllib2
import urllib
import SocketServer
import SimpleHTTPServer
import threading
import select
import socket
import cgi
import sys
import re

from urlparse import urlparse

import moxy.controllers
from moxy.config import Config
from moxy.http.strategies import MockStrategy

class MoxyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
	"""
	First responder for proxied HTTP requests
	"""
	def __init__(self, request, client_address, server):
		self.strategy = MockStrategy()
		self.config = config
		SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self, request, client_address, server)
	
	def do_PUT(self):
		self.invoke_with_strategy('do_PUT')	

	def do_DELETE(self):
		self.invoke_with_strategy('do_DELETE')

	def do_POST(self):
		self.invoke_with_strategy('do_POST')

	def do_GET(self):
		self.invoke_with_strategy('do_GET')

	def do_CONNECT(self):
		"""
		Establish tunnel and send SSL traffic
		through
		"""
		host, port = self.path.split(':')
		if not host or not port:
			self.send_response(400)
			return
		
		tunnel = socket.socket()

		try:
			tunnel.connect((host, int(port)))
			self.send_response(200, 'Connection Established')
			self.send_headers("Proxy-agent: Moxy/" + str(__version__) + "\r\n")
	
			timeout = 10000
			sockets = [self.connection, tunnel]
			time = 0
			while True:
				time += 5
				(recv, _, error) = select.select(sockets, [], sockets, 5)
				if time == timeout:
					break
				if error:
					break
				if recv:
					for s in recv:
						data = s.recv(8192)
						if s is self.connection:
							out = tunnel
						else:
							out = self.connection
						if data:
							out.send(data)
							time = 0
		except:
			print "Unexpected error:", sys.exc_info()[0]
			self.send_response(400)
			raise
		finally:
			tunnel.close()
	
	def invoke_with_strategy(self, func):
		"""
		Search for a strategy to handle the request
		method or use the default if none is found
		"""
		strategy = config.find_strategy(self.path)
		if strategy:
			getattr(strategy, func)(self)
			return

		getattr(self.strategy, func)(self)

	def forward_request(self, url, data=None):
		"""
		Send HTTP request to destination server and
		write headers, response code, and response
		"""
		opener = urllib2.build_opener(urllib2.HTTPHandler, 
			MoxyHTTPErrorProcessor, 
			urllib2.ProxyHandler({}))
		f = opener.open(urllib2.Request(url, data, self.headers))
		self.send_response(f.getcode())
		self.send_headers(str(f.info()))
		self.send_body(f)
		f.close()

	def get_post_data(self):
		"""
		Get POST data from HTTP request, if it exists
		"""
		length = self.headers.getheader('content-length')
		if not length:
			return None

		return self.rfile.read(int(length))

	def send_headers(self, data):
		"""
		Write HTTP headers into response
		"""
		self.wfile.write(data)
		self.end_headers()

	def send_response(self, code, message=None):
		"""
		Send HTTP response code
		"""
		self.log_request(code)
		if message is None:
			if code in self.responses:
				message = self.responses[code][0]
			else:
				message = ''
		if self.request_version != 'HTTP/0.9':
			self.wfile.write("%s %d %s\r\n" % 
				(self.protocol_version, code, message))

	def send_body(self, f):
		"""
		Copy a file into the response
		"""
		self.copyfile(f, self.wfile)
		self.wfile.flush()

class DaemonHandler(MoxyHandler):
	"""
	Handles requests for managing the proxy, such as
	displaying and refreshing the configuration
	"""
	def __init__(self, request, client_address, server):
		self.postvars = {}
		MoxyHandler.__init__(self, request, client_address, server)

	def do_POST(self):
		ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
		if ctype == 'multipart/form-data':
			self.postvars = cgi.parse_multipart(self.rfile, pdict)
		elif ctype == 'application/x-www-form-urlencoded':
			length = int(self.headers.getheader('content-length'))
			self.postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
			print self.postvars

		self.do_GET()

	def do_GET(self):
		path = urllib.unquote(urlparse(self.path).path).split('/')
		obj = None
		func = None
		for segment in path:
			if not segment: continue
			# Replace non-valid characters with _
			segment = re.sub(r'[^a-zA-Z0-9_]', '_', segment.lower())
			if not obj: 
				obj = getattr(moxy.controllers, segment.capitalize() + 'Controller')()
				continue
			elif not func:
				func = segment
			else:
				func += segment.capitalize()
		if func:
			getattr(obj, func)(self)
		elif obj:
			obj.index(self)
	
class MoxyHTTPErrorProcessor(urllib2.HTTPErrorProcessor):
	"""
	Since this is a proxy, we don't want to do any special
	error handling. We let the client take care of it.
	"""
	def http_response(self, req, response):
		return response

def start_proxy():
	"""
	Start proxying requests. A new process is forked for each
	incoming request
	"""
	SocketServer.ForkingTCPServer.allow_reuse_address = 1
	httpd = SocketServer.ForkingTCPServer(('', config.port), MoxyHandler)
	print '\nMoxy is listening on port %i' % config.port
	httpd.serve_forever()

def start_daemon():
	"""
	Start HTTP server to provide an interface for managing
	the proxy
	"""
	SocketServer.TCPServer.allow_reuse_address = 1
	httpd = SocketServer.TCPServer(('', config.port + 1), DaemonHandler)
	print '\nMoxy management daemon is listening on port %i' % (config.port + 1)
	httpd.serve_forever()

config = Config()

def main():
	config.load()

	t = threading.Thread(target=start_daemon)
	t.daemon = True
	t.start()

	start_proxy()
	
if __name__ == '__main__':
	main()
