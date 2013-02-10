__author__ = "Neil Loknath"
__copyright__ = "Copyright (c) 2013, Neil Loknath"
__license__ = "BSD"
__maintainer__ = "Neil Loknath"
__email__ = "nloko@nloko.ca"

import time
from moxy.logical import *

class DelayCondition(Condition):
	def __init__(self, expr_tree, delay):
		super(DelayCondition, self).__init__(expr_tree)
		self.delay = delay and int(delay) or None

	def perform(self, o):
		o._sleep(self.delay)

class HeaderCondition(Condition):
	def __init__(self, expr_tree, k, v):
		super(HeaderCondition, self).__init__(expr_tree)
		self.key = k
		self.value = v

	def perform(self, o):
		o[self.key] = self.value + '\r\n'

class ResponseCondition(Condition):
	def __init__(self, expr_tree, method, code, path):
		super(ResponseCondition, self).__init__(expr_tree)
		self.method = method
		self.code = int(code)
		self.path = path

	def perform(self, o):
		return (self.code, self.path)

class MockStrategy(object):
	"""
	A mock strategy for a given URL

	We can mock headers, and a response code and body
	for each HTTP request method.
	We can also add a delay to sleep for some number
	of seconds before servicing the request
	"""
	def __init__(self, url=None):
		self.url = url
		self.conditions = {'delay': set(), 'header': set(), 'response': set()}

	def __deepcopy__(self, memo):
		import copy
		c = MockStrategy(self.url)
		c.conditions = copy.deepcopy(self.conditions)
		return c

	def extend(self, o):
		self.append_conditions(o)

	def get_header_string(self, headers=None):
		if not headers:
			return ''	
		return ''.join([k + ':' + v for k, v in headers.iteritems()])

	def append_conditions(self, strategy):
		for k in strategy.conditions.keys():
			self.conditions[k].update(strategy.conditions[k])
	
	def add_delay_condition(self, condition):
		self.conditions['delay'].add(condition)

	def add_header_condition(self, condition):
		self.conditions['header'].add(condition)

	def add_response_condition(self, condition):
		self.conditions['response'].add(condition)

	def __evaluate_condition(self, moxy, condition):
		return condition.evaluate(moxy.config.evaluate_condition)

	def __perform_send_headers(self, moxy):
		headers = {}
		for c in self.conditions['header']:
			if self.__evaluate_condition(moxy, c):
				c.perform(headers)

		moxy.send_headers(self.get_header_string(headers))

	def __get_response(self, moxy, method='get'):
		for c in self.conditions['response']:
			if method == c.method and self.__evaluate_condition(moxy, c):
				return c.perform(self)

	def __perform_delay(self, moxy):
		for c in self.conditions['delay']:
			if self.__evaluate_condition(moxy, c):
				c.perform(self)
				return
		self._sleep()

	def do_GET(self, moxy):
		self.__do(moxy, self.__get_response(moxy))

	def do_PUT(self, moxy):
		self.__do(moxy, self.__get_response(moxy, 'put'))

	def do_DELETE(self, moxy):
		self.__do(moxy, self.__get_response(moxy, 'delete'))

	def do_POST(self, moxy):
		self.__do(moxy, self.__get_response(moxy, 'post'))

	def _sleep(self, delay=None):
		if not delay:
			return

		print 'Sleeping for %i' % delay
		time.sleep(delay / 1000)

	def __do(self, moxy, response):
		self.__perform_delay(moxy)
		if response is None:
			moxy.forward_request(moxy.path, moxy.get_post_data())	
			return

		code, path = response 
		moxy.send_response(code)
		self.__perform_send_headers(moxy)
		f = open(path, 'r')
		moxy.send_body(f)
		f.close()
