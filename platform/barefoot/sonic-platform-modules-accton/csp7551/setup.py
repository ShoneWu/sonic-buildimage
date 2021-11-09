#!/usr/bin/env python

import os
import sys
from setuptools import setup
os.listdir

setup(
   name='csp7551',
   version='1.0',
   description='Module to initialize Accton csp7551 platforms',
   
   packages=['csp7551'],
   package_dir={'csp7551': 'csp7551/classes'},
)
