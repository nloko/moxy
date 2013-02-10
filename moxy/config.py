__author__ = "Neil Loknath"
__copyright__ = "Copyright (c) 2013, Neil Loknath"
__license__ = "BSD"
__maintainer__ = "Neil Loknath"
__email__ = "nloko@nloko.ca"

import re
import copy

from collections import OrderedDict
from http.strategies import * 
from logical import *

class ConfigParser(object):
	def __init__(self):
		self.strategies = OrderedDict() 
		self.port = None
		self.conditions = set()

	def process(self, f):
		"""
		Process config file
		"""
		strategy = None
		for line in f:
			condition, line = self.__process_condition(line)
			line = line.split()
			if not line:
				continue

			#print condition, line
			line[0] = line[0].lower()

			if line[0] == 'port' and line[1].isdigit():
				self.port = line[1]
			elif line[0] == 'url' and len(line) > 1:
				strategy = MockStrategy(line[1])
				self.__add_strategy(strategy)

			self.__process_strategy(line, strategy, condition)

	def __process_condition(self, line):
		condition = None
		if line.strip().startswith('if'):
			condition, line = map(lambda s: s.strip(), line.split(':', 1))
			condition = Grammer.top(Grammer(condition).parse())[1:]
			#print 'process', condition
		return (condition, line)
	
	def __process_strategy(self, line, strategy=None, condition=['default']):
		if not strategy:
			return
		if not condition:
			condition = ['default']

		tree = None

		if line[0] == 'delay' and len(line) > 1:
			delay = len(line) > 1 and int(line[1]) or 5000
			tree = build_expr_tree(condition)
			strategy.add_delay_condition(DelayCondition(tree,  
					delay))
		elif line[0] == 'header' and len(line) > 2:
			key, value = line[1], ' '.join(line[2:])
			tree = build_expr_tree(condition)
			strategy.add_header_condition(HeaderCondition(tree,
				key,
				value))
		elif line[0] in ('get', 'post', 'delete', 'put') and len(line) > 1:
			method = line[0]
			code = int(line[1])
			body_path = len(line) > 2 and line[2] or None
			tree = build_expr_tree(condition)
			strategy.add_response_condition(ResponseCondition(tree,
				method,
				code,
				body_path))

		if tree:
			map(self.conditions.add, [n.value for n in get_leaves(tree)])
	
	def __add_strategy(self, s):
		self.strategies[s.url] = s

class Config(object):
	"""
	Manage loading and storing configuration 
	details
	"""
	FILE_PATH = 'moxy.conf'
	
	def __init__(self):
		self.__port = 8080
		self.strategies = None 
		self.cond_table = {'default': 1}
		self.conditions = set()

	@property
	def port(self):
		return self.__port

	@port.setter
	def port(self, value):
		value = int(value)
		if 1024 <= value < 2**16:
			self.__port = value
 
	def get_file(self):
		"""
		Get config file as read-only file object
		"""
		return open(self.FILE_PATH, 'r')

	def load(self):
		"""
		Load the config settings from disk to memory
		"""
		configFile = self.get_file()
		parser = ConfigParser()
		parser.process(configFile)
		configFile.close()
		self.port = parser.port
		self.strategies = parser.strategies

		map(lambda k: self.cond_table.pop(k), self.conditions - parser.conditions)
		self.conditions = (parser.conditions - self.conditions) | parser.conditions
		map(self.update_cond_table, self.conditions)

	def find_strategy(self, url):
		"""
		Each section of the config file represents a mock
		strategy for a given URL pattern. Since several
		patterns may match a URL, we consolidate matching
		strategies into one.
		"""
		if url in self.strategies:
			return self.strategies[url]

		matches = []
		for k, v in self.strategies.iteritems():
			match = re.match(k, url)
			if match:
				matches.append(v) 

		if not matches:
			return None
		elif len(matches) == 1:
			return matches[0]

		strategy = copy.deepcopy(matches[0])
		
		for match in matches[1:]:
			strategy.extend(match)

		return strategy

	def evaluate_condition(self, condition):
		if not condition in self.cond_table:
			return False
		return self.cond_table[condition]

	def update_cond_table(self, value):
		if value not in self.cond_table:
			self.cond_table[value] = 0
