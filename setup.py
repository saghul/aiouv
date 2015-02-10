# coding: utf-8

# Release procedure:
#  - fill the changelog?
#  - run tests
#  - update version in setup.py
#  - set release date in the changelog?
#  - check that "python setup.py sdist" contains all files tracked by
#    the Mercurial: update MANIFEST.in if needed
#  - git commit
#  - git tag VERSION
#  - git push
#  - git push --tags
#  - python setup.py register sdist bdist_wheel upload
#  - increment version in setup.py
#  - git commit && git push

import os
import sys
try:
    from setuptools import setup
    SETUPTOOLS = True
except ImportError:
    SETUPTOOLS = False
    # Use distutils.core as a fallback.
    # We won't be able to build the Wheel file on Windows.
    from distutils.core import setup

with open("README.rst") as fp:
    long_description = fp.read()

requirements = ["pyuv>=1.0"]
if sys.version_info < (3, 4):
    requirements.append("asyncio>=0.4.1")

install_options = {
    "name": "aiouv",
    "version": "0.0.1",
    "license": "MIT license",
    "author": 'Saúl Ibarra Corretgé',

    "description": "libuv based event loop for asyncio",
    "long_description": long_description,
    "url": "http://github.com/saghul/aiouv",

    "classifiers": [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
    ],

    "packages": ["aiouv"],
#    "test_suite": "runtests.runtests",
}
if SETUPTOOLS:
    install_options['install_requires'] = requirements

setup(**install_options)
