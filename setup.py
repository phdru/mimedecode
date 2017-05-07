#! /usr/bin/env python

try:
    from setuptools import setup
    is_setuptools = True
except ImportError:
    from distutils.core import setup
    is_setuptools = False

kw = {}
if is_setuptools:
    kw['install_requires'] = ['m_lib.defenc>=1.0']
    kw['tests_require'] = ['m_lib>=3.1']

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
    keywords=['email', 'MIME'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 2 :: Only',
    ],
    py_modules = ['mimedecode_version'],
    scripts = ['mimedecode.py'],
    **kw
)
