#!/usr/bin/env python

import os
from setuptools import setup
os.listdir

setup(
   name='as9926_24d',
   version='1.0',
   description='Module to initialize Accton AS9926-24D platforms',

   packages=['as9926_24d'],
   package_dir={'as9926_24d': 'as9926-24d/classes'},
)

