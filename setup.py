# -*- coding: utf-8 -*-
'''
Created on 2018. 9. 19.
@author: Hyechurn Jang, <hyjang@cisco.com>
'''

import os
from setuptools import setup

def read(fname): return open(os.path.join(os.path.dirname(__file__), fname)).read()
setup(
    name='pygics',
    version='0.8.4',
    license='Apache 2.0',
    author='Hyechurn Jang',
    author_email='hyjang@cisco.com',
    url='https://github.com/HyechurnJang/pygics',
    description='Python Gevent Interface for Communication Service',
    long_description=read('README'),
    long_description_content_type="text/markdown",
    packages=['pygics'],
    install_requires=['jzlib', 'gevent', 'requests'],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)

# python sdist bdist_wheel
# twine upload dist/*