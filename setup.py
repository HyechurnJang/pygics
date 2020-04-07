# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2020. 3. 18..
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

import os
from setuptools import setup


def read(fname): return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='pygics',
    version='1.1.0',
    license='Apache 2.0',
    author='Hyechurn Jang',
    author_email='jangh@vmware.com',
    url='https://github.com/HyechurnJang/pygics',
    description='Python Gevent Interface for Communication Service',
    long_description=read('README'),
    long_description_content_type="text/markdown",
    packages=['pygics'],
    package_data = {'pygics' : ['static/*']},
    install_requires=['gevent', 'requests', 'PyYAML', 'watchdog', 'watchdog_gevent', 'SQLAlchemy'],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
    ],
)

# python setup.py sdist bdist_wheel
# twine upload dist/*
