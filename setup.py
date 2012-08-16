#!/usr/bin/env python
# coding: utf-8
#
#  Copyright (c) 2012, Adam Turcotte (adam.turcotte@gmail.com)
#                      Nicolas Robidoux (nicolas.robidoux@gmail.com)
#  License: BSD 2-Clause License
#
#  This file is part of the 
#  EXQUIRES (EXtensible QUantitative Image RESampling) test suite
#

"""
setup.py for exquires.
"""

import os
import sys

if sys.version_info < (2, 7):
    raise Exception("EXQUIRES requires Python 2.7 or higher.")

from setuptools import setup, find_packages

from exquires import __version__ as VERSION


this_dir = os.path.abspath(os.path.dirname(__file__))

NAME = 'exquires'
PACKAGES = find_packages(exclude=['ez_setup'])
DESCRIPTION = 'EXQUIRES (EXtensible QUantitative Image RESampling) test suite'
URL = 'http://exquires.ca'
LICENSE = 'BSD 2-Clause (http://www.opensource.org/licenses/bsd-license.php)'
LONG_DESCRIPTION = open(os.path.join(this_dir, 'README.rst')).read()
requirements_file = open(os.path.join(this_dir, 'requirements.txt'))
REQUIREMENTS = filter(None, requirements_file.read().splitlines())
DATA_FILES = ['wave.tif', 'sRGB_IEC61966-2-1_black_scaled.icc', 'examples/*']
AUTHOR = 'Adam Turcotte'
AUTHOR_EMAIL = 'adam.turcotte@gmail.com'
KEYWORDS = ('image', 'reconstruction', 'enlargement',
            'upsampling', 'test', 'testing')
CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Topic :: Multimedia :: Graphics',
    'Topic :: Software Development :: Testing'
]
CONSOLE_SCRIPTS = [
    'exquires-aggregate = exquires.aggregate:main',
    'exquires-compare = exquires.compare:main',
    'exquires-correlate = exquires.correlate:main',
    'exquires-new = exquires.new:main',
    'exquires-report = exquires.report:main',
    'exquires-run = exquires.run:main',
    'exquires-update = exquires.update:main'
]

params = dict(
    name=NAME,
    version=VERSION,
    packages=PACKAGES,
    install_requires=REQUIREMENTS,
    package_data={'exquires': DATA_FILES},
    exclude_package_data={'exquires': ['*.pyc']},

    # Metadata for PyPI.
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    license=LICENSE,
    keywords=KEYWORDS,
    url=URL,
    classifiers=CLASSIFIERS,
    entry_points={'console_scripts': CONSOLE_SCRIPTS}
)

setup(**params)
