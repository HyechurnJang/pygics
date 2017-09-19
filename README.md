# pygics

**PY**thon **G**event **I**nterface for **C**orresponding **S**ervice

version : 0.5.5

last change : add static content type 

## What is Pygics?

<p align="center"><img src="./doc/pygics_logo.png"></p>

Gevent which is event-based processing is good for using CPU performance with efficient.<br/>
But it have to make code optimization and use specific APIs for your code.<br/>
For solving issue under legacy code, Gevent supply monkey patching however it make to odd penomenons.<br/>
So Pygics is made of wrapping Gevent for unified platform which is used corresponding service.<br/>

Now, pygics is used following

 - Concurrency Tasking
 - RestAPI Wrapper
 - Micro Service
    - Prepared Applications : https://github.com/pygics-app
    - Experimental Applications : https://github.com/pygics-app-exp

See the document below for more details.

## Install

Pygics Installation is available via PyPI and Git Source.

**From PIP**

	$ pip install pygics

**From GIT**

	$ python setup.py build
	$ python setup.py install

## Examples

**you should get sample code in "sample" directory**

### Tasking

#### Basic Task Example

	# import Pygics Package
	import pygics
	
	# define your task with inheritant Task from pygics
	#
	# "__init__" has parameter following
	# tick : task execute every "tick" sec. default is 0 sec, task looping immediately
	# delay : task execute after "delay" sec on first start. default is 0 sec, executing immediately
	# debug : print execution error. default is False
	#
	# override "run" method with your task logic.
	class YourTask(pygics.Task):
	    
	    def __init__(self, name, tick, delay):
	        pygics.Task.__init__(self, tick, delay)
	        self.name = name
	        self.start()
	        
	    def run(self):
	        print self.name
	
	t1 = YourTask('Task1', 2, 1) # execute every 2 sec, delayed 1 sec
	t2 = YourTask('Task2', 3, 2) # execute every 3 sec, delayed 2 sec
	
	pygics.Time.sleep(10) # sleep main task until 10 sec 
	
	t2.stop() # stop "t2" task
	
	pygics.Time.sleep(5) # sleep main task until 5 sec
	
	t1.stop() # stop "t1" task

#### Tasking Utils

##### Sleep

	from pygics import Time
	
	Time.sleep(10) # sleep 10 sec

##### Queue

	from pygics import Queue
	
	q = Queue() # create Queue
	q.put("data") # put "data" to Queue
	data = q.get() # get "data" from Queue

##### Lock

	from pygics import Lock
	
	lock = Lock() # create Lock
	lock.acquire() # locking
	lock.release() # unlocking

#### Bursting

	import pygics
	
	def getSum(a, b):
	    pygics.Time.sleep(4)
	    return a + b
	
	def getMul(a, b):
	    pygics.Time.sleep(2)
	    return a * b
	
	getSum_ret, getMul_ret = pygics.Burst().register(getSum, 1, 1).register(getMul, 1, 1).do()
	print getSum_ret, getMul_ret
	>>> 2 1 # print after 4 sec which is set getSum's sleep

### Session

	from pygics RestAPI
	
	class YourSession(RestAPI): # define your session with inheritant RestAPI from pygics
	    
	    # need to implement method following
	    def __login__(self, req): # login logic
	        # Return Token
	        return None
	    
	    def __refresh__(self, req): # session refreshing logic
	        # Return Token
	        return None
	    
	    def __header__(self): # dict formatted header data for every messaging header
	        # Return Headers
	        return None
	    
	    def __cookie__(self): # dict formatted cookie data for every messaging header
	        # Return Cookies
	        return None
	
	s = YourSession("http://your/site", "yourId", "yourPassword")
	resp = s.get("/calling/your/api")

### Service

	import pygics
	
	pygics.server('0.0.0.0', 80) # listening IP and port

