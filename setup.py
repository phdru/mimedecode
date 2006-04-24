#! /usr/bin/env python


from distutils.core import setup
from mimedecode import __version__ as version


setup(name = "mimedecode",
   version = version + 'd',
   description = "BroytMann mimedecode.py",
   long_description = "BroytMann mimedecode.py, Copyright (C) 2001-2004 PhiloSoft Design",
   author = "Oleg Broytmann",
   author_email = "phd@phd.pp.ru",
   url = "http://phd.pp.ru/Software/Python/#mimedecode",
   license = "GPL",
   platforms = "All",
   scripts = ['mimedecode.py']
)
