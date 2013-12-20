#! /usr/bin/env python

from distutils.core import setup
from mimedecode_version import __version__, __copyright__, __license__

setup(name = "mimedecode",
   version = __version__,
   description = "A program to decode MIME messages",
   long_description = "A program to decode MIME messages. " + __copyright__,
   author = "Oleg Broytman",
   author_email = "phd@phdru.name",
   url = "http://phdru.name/Software/Python/#mimedecode",
   license = __license__,
   platforms = "All",
   py_modules = ['mimedecode_version'],
   scripts = ['mimedecode.py']
)
