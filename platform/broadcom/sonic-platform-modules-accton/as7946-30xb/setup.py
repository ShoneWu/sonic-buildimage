#!/usr/bin/env python

import os
from setuptools import setup
os.listdir

setup(
   name='as7946_30xb',
   version='1.0',
   description='Module to initialize Accton AS7946-30XB platforms',

   packages=['as7946_30xb'],
   package_dir={'as7946_30xb': 'as7946-30xb/classes'},
)

