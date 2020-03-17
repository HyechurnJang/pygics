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
    version='1.0.0',
    license='Apache 2.0',
    author='Hyechurn Jang',
    author_email='jangh@vmware.com',
    url='https://github.com/HyechurnJang/pygics',
    description='Python Gevent Interface for Communication Service',
    long_description=read('README'),
    long_description_content_type="text/markdown",
    packages=['pygics'],
    install_requires=['gevent', 'requests', 'PyYAML', 'watchdog', 'watchdog_gevent', 'SQLAlchemy'],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
    ],
)

# python setup.py sdist bdist_wheel
# twine upload dist/*