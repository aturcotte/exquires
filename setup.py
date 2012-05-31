#!/usr/bin/env python
# coding: utf-8
#
#  Copyright (c) 2012, Adam Turcotte (adam.turcotte@gmail.com)
#                      Nicolas Robidoux (nicolas.robidoux@gmail.com)
#  License: BSD 2-Clause License
#
#  This file is part of
#  EXQUIRES | Evaluative and eXtensible QUantitative Image Re-Enlargement Suite
#

"""
setup.py for exquires.
"""

import os

from setuptools import setup, find_packages

from exquires import __version__ as VERSION


this_dir = os.path.abspath(os.path.dirname(__file__))

NAME = 'exquires'
PACKAGES = find_packages(exclude=['ez_setup'])
DESCRIPTION = 'EXQUIRES - Evaluative and eXtensible QUantitative Image Re-Enlargement Suite'
URL = 'http://exquires.rivetsforbreakfast.com'
LICENSE = 'BSD 2-Clause License'
LONG_DESCRIPTION = open(os.path.join(this_dir, 'README.rst')).read()
requirements_file = open(os.path.join(this_dir, 'requirements.txt'))
REQUIREMENTS = filter(None, requirements_file.read().splitlines())
DATA_FILES = ['wave.tif', 'sRGB_IEC61966-2-1_black_scaled.icc']
AUTHOR = 'Adam Turcotte'
AUTHOR_EMAIL = 'adam.turcotte@gmail.com'
KEYWORDS = ('image', 'reconstruction', 'enlargement', 'upsampling', 'test', 'testing')
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
    package_data={'exquires': DATA_FILES}

    # Metadata for PyPI.
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    keywords=KEYWORDS,
    url=URL,
    classifiers=CLASSIFIERS,
    entry_points={'console_scripts': CONSOLE_SCRIPTS}
)

setup(**params)
