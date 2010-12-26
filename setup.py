#! /usr/bin/env python

from distutils.core import setup
from mimedecode import _version, __copyright__

setup(name = "mimedecode",
   version = _version,
   description = "Broytman mimedecode.py",
   long_description = "Broytman mimedecode.py, " + __copyright__,
   author = "Oleg Broytman",
   author_email = "phd@phdru.name",
   url = "http://phdru.name/Software/Python/#mimedecode",
   license = "GPL",
   platforms = "All",
   scripts = ['mimedecode.py']
)
