import os
from setuptools import setup

def read(fname): return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='pygics',
    version='0.1.1',
    license='Apache 2.0',
    author='Hyechurn Jang',
    author_email='hyjang@cisco.com',
    url='https://github.com/HyechurnJang/pygics',
    description='Python Service Library',
    long_description=read('README'),
    packages=['pygics'],
    classifiers=[
      'Development Status :: 4 - Beta',
      'License :: OSI Approved :: Apache Software License',
      'Intended Audience :: Developers',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 2.7',
      'Topic :: Software Development :: Libraries :: Python Modules',
      'Operating System :: POSIX',
      'Operating System :: POSIX :: Linux',
      'Operating System :: MacOS',
      'Operating System :: MacOS :: MacOS X',
    ],
    install_requires=[]
)
