# pygics

**PY**thon **G**event **I**nterface for **C**ommunication **S**ervice

version : 1.0.0

last change : new launch 1.0.0

## What is Pygics?

<p align="center"><img src="./doc/pygics_logo_new.png"></p>

Gevent which is event-based processing is good for using CPU performance with efficient.<br/>
But it have to make code optimization and use specific APIs for your code.<br/>
For solving issue under legacy code, Gevent supply monkey patching however it make to odd penomenons.<br/>
So Pygics is made of wrapping Gevent for unified platform which is used corresponding service.<br/>

Now, pygics is used following

 - Concurrency Tasking
 - RestAPI Wrapper
 - Micro Service

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
