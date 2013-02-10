import urllib
import sys

class Controller(object):
	def write_from_file(self, handler, code, path):
		handler.send_response(code)
		handler.send_headers('')
		f = open(path, 'r')
		handler.send_body(f)
		f.close()

class CssController(Controller):
	def index(self, handler):
		self.main(handler)

	def main(self, handler):
		self.write_from_file(handler, 200, 'templates/css/moxy.css')

class ConfigController(Controller):
	def index(self, handler):
		self.main(handler)

	def main(self, handler):
		self.write_from_file(handler, 200, 'templates/config.html')

	def show(self, handler):
		self.write_from_file(handler, 200, handler.config.FILE_PATH)

	def showMeTheFile(self, handler):
		self.show(handler)

	def refresh(self, handler):
		try:
			handler.config.load()
			self.write_from_file(handler, 200, 'templates/config_success.html')
		except:
			print sys.exc_info()[0]			
			self.write_from_file(handler, 200, 'templates/config_error.html')

	def conditions(self, handler):
		cond_table = handler.config.cond_table
		conditions = handler.config.conditions

		if handler.postvars and 'id' in handler.postvars:
			cond = urllib.unquote(handler.postvars['id'][0])
			if not cond in cond_table:
				handler.send_response(400)
				return
			cond_table[cond] = not cond_table[cond]

		handler.send_response(200)
		handler.send_headers('')
		f = open('templates/conditions.html', 'r')
		html = f.read()
		f.close()

		html_body = ''
		for c in conditions:
			safe_c = urllib.quote(c)
			html_body += """
			<tr>
				<td>
					<a href='#' onclick=\"setItem('%s');\">%s</a>
				</td>
				<td>
					%s
				</td>
			</tr>
			""" % (safe_c, safe_c, cond_table[c] and 'True' or 'False')
		handler.wfile.write(html.replace('$rows', html_body, 1))
