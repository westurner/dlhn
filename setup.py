#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

import os
import re

from setuptools import setup, find_packages

PKGNAME = 'dlhn'

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

def get_property(prop, project):
    with open(os.path.join(project, '__init__.py')) as _file:
        result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop),
                _file.read())
    return result.group(1)

VERSION = get_property('__version__', PKGNAME)

requirements = [
    'beautifulsoup4',
    'bleach',
    'certifi',
    'jinja2',
    'requests',
    'urlobject',
    'requests-cache',
]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

setup(
    author="Wes Turner",
    author_email='wes@wrd.nu',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description=(
        'dlhn is a Python CLI script to download my comments'
        ' and submissions from the Hacker News API'
        ' and generate a static HTML archive with a Jinja2 template'),
    install_requires=requirements,
    license="BSD license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='%s' % PKGNAME,
    name=PKGNAME,
    packages=find_packages(include=[PKGNAME]),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/westurner/dlhn',
    version=VERSION,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'dlhn=dlhn.dlhn:main'
        ]
    },
)
