#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

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
        ' and submissions from the Firebase HackerNews API'
        ' and generate a static HTML archive with a Jinja2 template'),
    install_requires=requirements,
    license="BSD license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='dlhn',
    name='dlhn',
    packages=find_packages(include=['dlhn']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/westurner/dlhn',
    version='0.1.0',
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'dlhn=dlhn.dlhn:main'
        ]
    },
)
