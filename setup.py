#! /usr/bin/env python

from imp import load_source
from os.path import abspath, dirname, join

try:
    from setuptools import setup
    is_setuptools = True
except ImportError:
    from distutils.core import setup
    is_setuptools = False

versionpath = join(abspath(dirname(__file__)), "mimedecode", "__version__.py")
load_source("mimedecode_version", versionpath)
from mimedecode_version import __version__, __copyright__, __license__ # noqa: ignore flake8 E402

kw = {}
if is_setuptools:
    kw['install_requires'] = ['m_lib.defenc>=1.0']
    kw['tests_require'] = ['m_lib>=3.1']
    kw['python_requires'] = '>=2.7, !=3.0.*, !=3.1.*, !=3.2.*'


setup(
    name="mimedecode",
    version=__version__,
    description="A program to decode MIME messages",
    long_description="A program to decode MIME messages. " + __copyright__,
    author="Oleg Broytman",
    author_email="phd@phdru.name",
    url="http://phdru.name/Software/Python/#mimedecode",
    license=__license__,
    keywords=['email', 'MIME'],
    platforms="Any",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=['mimedecode'],
    entry_points={
        'console_scripts': [
            'mimedecode = mimedecode.__main__:main'
        ]
    },
    **kw
)
