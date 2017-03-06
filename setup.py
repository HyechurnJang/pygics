import os
from setuptools import setup

def read(fname): return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='pygics',
    version='0.1.2',
    license='Apache 2.0',
    author='Hyechurn Jang',
    author_email='hyjang@cisco.com',
    url='https://github.com/HyechurnJang/pygics',
    description='Python Gevent Interface for Coresponding Service',
    long_description=read('README'),
    packages=['pygics'],
    install_requires=['gevent', 'requests']
)
