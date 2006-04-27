#! /usr/bin/env python


from distutils.core import setup
from mimedecode import _version, __copyright__


setup(name = "mimedecode",
   version = _version,
   description = "BroytMann mimedecode.py",
   long_description = "BroytMann mimedecode.py, " + __copyright__,
   author = "Oleg Broytmann",
   author_email = "phd@phd.pp.ru",
   url = "http://phd.pp.ru/Software/Python/#mimedecode",
   license = "GPL",
   platforms = "All",
   scripts = ['mimedecode.py']
)
