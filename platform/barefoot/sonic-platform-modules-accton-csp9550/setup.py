#!/usr/bin/env python

import os
import sys
from setuptools import setup
os.listdir

setup(
   name='csp9550',
   version='1.1',
   description='Module to initialize Accton CSP9550 platforms',
   
   packages=['csp9550'],
   package_dir={'csp9550': ''},
)
