#Moxy

Moxy is an HTTP proxy that allows mocking of HTTP responses, 
including support for delays and conditional statements.

##What and Why?

Moxy has 2 main goals:

- Be simple, it's real easy to get it up and running
- Improve developer efficiency, allow a client application developer to work
even without a fully developed backend HTTP service they require
 
Sometimes when working in a team, a service required by the client application
development team may take some time to develop. Since the client team can code
without the service existing (as long as the interface for the service has been
defined), the client team should be able to test without the service existing as
well.
 
##How?

Start Moxy from the command line by issuing:

	./moxy.py

...from the directory where Moxy resides. Moxy has no external dependancies.   
By default, Moxy uses port 8888 for the
proxy and port 8889 for its configuration service.

Now, configure your system to use localhost:8888 as an HTTP proxy and you're 
ready to start mocking HTTP responses.

All behaviour is defined in `moxy.conf`. Let's examine the default `moxy.conf` to 
learn how we can alter the responses to HTTP requests.

	url http://api.awesomeapp.com/v1/awesome/?$
	  get 200 awesome.json

	url http://api.awesomeapp.com/v1/awesome/add
	  if delay_add: delay 13000
	  get 400 awesome_add_error.json
	  post 200 awesome_add.json

	url http://api.awesomeapp.com/v1/awesome/?\?id\=.+
	  get 400 awesome_id_error.json
	  if created: get 200 awesome_id.json

### URL

Each entry in `moxy.conf` must start with a *url* statement
The format is:

	url regex

*regex* is a regular expression that matches the URL of an HTTP request.

### Response

A different response can be specified for each supported HTTP method.

The format is:

	method code [file]

*method* is the HTTP method. GET, POST, PUT, and DELETE are supported.  
*code* is the response code to return for the matched request.  
*file* is optional. It specifies a file in the directory where moxy is running. Its
contents will be used for the response body.

### Headers

The format is:
	
	header name value

*name* is the name part of the header field  
*value* is the value part of the header field
 
### Delay

The format is:

	delay [n]

*n* is optional. It's the number of milliseconds to wait before servicing the request. If not specified,
the delay will be 5000ms or 5 seconds.

### Conditional Statements

Conditional statements can be prefixed to any line except *url*.
Remember that the first conditonal statement to evaluate to *true*
will be the one used. Order of statements is important.

The format is:

	if expr:

*expr* is a logical expression. Valid operators are *not*, *and*, and *or*.  
Parentheses are supported.

Each operand in the expression will create a *condition* within Moxy. 
Conditions can be reused in more than one statement.  

Conditions can be viewed at `http://localhost:8889/conditions`. Here, values 
can be toggled in order to satisfy/unsatisfy conditional statements.
