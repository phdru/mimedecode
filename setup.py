#! /usr/bin/env python

from os.path import abspath, dirname, join
from setuptools import setup
import sys

versionpath = join(abspath(dirname(__file__)), 'mimedecode', '__version__.py')
mimedecode_version = {}

if sys.version_info[:2] == (2, 7):
    execfile(versionpath, mimedecode_version)  # noqa: F821 'execfile' Py3

elif sys.version_info >= (3, 4):
    exec(open(versionpath, 'r').read(), mimedecode_version)

else:
    raise ImportError("mimedecode requires Python 2.7 or 3.4+")

setup(
    name="mimedecode",
    version=mimedecode_version['__version__'],
    description="A program to decode MIME messages",
    long_description="A program to decode MIME messages. " +
    mimedecode_version['__copyright__'],
    long_description_content_type="text/plain",
    author="Oleg Broytman",
    author_email="phd@phdru.name",
    url="https://phdru.name/Software/Python/#mimedecode",
    project_urls={
        'Homepage': 'https://phdru.name/Software/Python/#mimedecode',
        'Documentation': 'https://phdru.name/Software/Python/mimedecode.html',
        'Download':
            'https://phdru.name/Software/Python/'
            'mimedecode-%s.tar.bz2' % mimedecode_version['__version__'],
        'Git repo': 'https://git.phdru.name/mimedecode.git',
        'Github repo': 'https://github.com/phdru/mimedecode',
        'Issue tracker': 'https://github.com/phdru/mimedecode/issues',
    },
    license=mimedecode_version['__license__'],
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
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
    packages=['mimedecode'],
    entry_points={
        'console_scripts': [
            'mimedecode = mimedecode.__main__:main'
        ]
    },
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    install_requires=['m_lib.defenc>=1.0'],
    tests_require=['m_lib>=3.1'],
)
