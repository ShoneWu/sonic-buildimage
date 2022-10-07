#!/usr/bin/env python

import os
from setuptools import setup
os.listdir

setup(
   name='as7946_74xkb',
   version='1.0',
   description='Module to initialize Accton AS7946-74XKB platforms',

   packages=['as7946_74xkb'],
   package_dir={'as7946_74xkb': 'as7946-74xkb/classes'},
)

