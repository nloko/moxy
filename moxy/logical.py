__author__ = "Neil Loknath"
__copyright__ = "Copyright (c) 2013, Neil Loknath"
__license__ = "BSD"
__maintainer__ = "Neil Loknath"
__email__ = "nloko@nloko.ca"

import re

class Grammer:
	"""
	Defines the grammer of an if statement
	"""
	@classmethod
	def top(cls, tree):
		"""
		Returns a list of only the root nodes of each component.
		In other words, the returned list will not contain parsed
		sublists of expressions within parentheses
		"""
		#print 'top', tree
		l = []
		for n in tree:
			if len(n[0]) > 1:
				l.append(n[0])
			else:
				l.append(n)
		return l

	@classmethod
	def join_top(cls, top):
		def process(e):
			if len(e.split()) == 1:
				return e
			else:
				return '(' + e + ')'

		return ' '.join([process(e) for e in top])

	def __init__(self, statement):
		self.statement = statement

	def parse(self):
		"""
		Returns a parse tree as a list. Each element is either a
		terminal node (if, not, operator, or operand) or a subtree
		as another list. If an element is a subtree, the subtree 
		represents an expression within parentheses where the root
		is the unparsed expression
		"""
		return self.__parse_a(self.statement, [])

	def parse_expression(self):
		"""
		Returns a parse tree as a list. Parses considering
		only the expression part of an if statement.
		"""
		l = []
		self.__parse_b(self.statement, l)
		return l

	def __parse_a(self, a, l=[]):
		a = a.strip()

		if a[:2] != 'if':
			raise ValueError('not an if statement')

		l.append(a[:2])
		self.__parse_b(a[2:].strip(), l)

		return l

	def __parse_b(self, b, l):
		#print 'parse_b', b, l
		b = b.strip()

		if not b:
			return
		if b[:3] == 'not':
			l.append(b[:3])
			self.__parse_b(b[3:], l)
			return

		count = 0
		first = 0
		last = len(b)
		left = []

		if b[0] == '(':
			for i in range(0, len(b)):
				if b[i] == '(':
					count += 1
					continue
				elif b[i] == ')':
					count -= 1
					if count == 0:
						last = i
						left.append(b[first+1:i])
						break
		
			l.append(left)
			self.__parse_b(left[-1], left)
		else:
			pos = b.find(' ')
			if pos >= 0:
				last = pos
			left = l
			self.__parse_d(b[first:last], left)

		right = b[last+1:].split()
		if len(right) == 1:
			right = right[0].split()

		if not right:
			return
		self.__parse_c(right[0], l)
		self.__parse_b(' '.join(right[1:]), l)

	def __parse_c(self, c, l):
		#print 'parse_c', c, l

		if not re.match(r'^(and)|(or)$', c):
			raise ValueError('Invalid operand')

		l.append(c)

	def __parse_d(self, d, l):
		#print 'parse_d', d, l
		if not re.match(r'^\S+$', d.strip()):
			raise ValueError('Invalid operator')

		l.append(d.strip())

class Condition(object):
	def __init__(self, expr_tree):
		self.tree = expr_tree
		#print_expr_tree(self.tree)

	def evaluate(self, e):
		return self.tree.evaluate(e)

	def perform(self, o):
		pass

class Node(object):
	def __init__(self, value):
		self.value = value
		self.parent = None
		self.left = None
		self.right = None

	def evaluate(self, e):
		"""
		Evaluates using calling the passed function
		with the node's value as its argument
		returning True or False
		"""
		return e(self.value)

class NegationNode(Node):
	def __init__(self, node):
		self.node = node
		self.value = node.value
		self.left = node.left
		self.right = node.right

	def evaluate(self, e):
		return not self.node.evaluate(e)

class OperatorNode(Node):
	AND = 'and'
	OR = 'or'
	OPERANDS = (AND, OR)

	def __init__(self, value, left, right):
		super(OperatorNode, self).__init__(value.lower())
		if value not in OperatorNode.OPERANDS:
			raise ValueError('Unknown operator')
		left.parent = self
		right.parent = self
		self.left = left
		self.right = right

	def evaluate(self, e):
		"""
		Evaluate the logical expression by traversing
		the tree and returning True or False
		"""
		if self.value == OperatorNode.AND:
			return self.left.evaluate(e) and self.right.evaluate(e)
		elif self.value == OperatorNode.OR:
			return self.left.evaluate(e) or self.right.evaluate(e)
		else:
			raise ValueError('Unknown operator')

def get_leaves(node):
	"""
	Get the leaf nodes in the passed expression
	tree (the logical expression operands)
	"""
	if not node:
		return []

	leaves = []
	stack = [node]
	while stack:
		n = stack.pop()
		if not n:
			continue
		if not (n.left or n.right):
			leaves.append(n)
		else:
			stack.append(n.left)
			stack.append(n.right)
	return leaves

def print_expr_tree(node, depth=0):
	if not node:
		return

	if depth is 0:
		print 'printing expression tree...'

	print node.value, depth
	print_expr_tree(node.left, depth+1)
	print_expr_tree(node.right, depth+1)
	
def build_expr_tree(expr):
	"""
	Build an expression tree from the passed logical
	expression represented as a list where each item
	is either an operator or operand.
	"""
	if not expr:
		return None

	#print 'build_expr_tree', expr

	if len(expr) > 1 and expr[0].strip().lower() == 'not':
		return NegationNode(build_expr_tree(expr[1:]))

	if len(expr) == 1:
		expr = expr[0].split()
		if len(expr) == 1:
			return Node(expr[0])

	operand = 1
	
	if OperatorNode.OR in expr:
		operand = expr.index(OperatorNode.OR)
	
	left = get_parsed_expr(expr[0:operand])
	right = get_parsed_expr(expr[operand+1:])

	#print left, expr[operand], right	

	return OperatorNode(expr[operand], 
		build_expr_tree(left), 
		build_expr_tree(right))

def get_parsed_expr(expr):
	if len(expr) == 1:
		return expr
	return Grammer.top(Grammer(Grammer.join_top(expr)).parse_expression())
