#! /usr/bin/env python

try:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup
    is_setuptools = True
except ImportError:
    from distutils.core import setup
    is_setuptools = False

kw = {}
if is_setuptools:
    kw['setup_requires'] = ['m_lib']
    kw['install_requires'] = ['m_lib']
    kw['dependency_links'] = [
        'http://phdru.name/Software/Python/#egg=m_lib',
        'git+http://git.phdru.name/m_lib.git#egg=m_lib',
         'git+git://git.phdru.name/m_lib.git#egg=m_lib',
    ]

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
   scripts = ['mimedecode.py'],
   **kw
)
