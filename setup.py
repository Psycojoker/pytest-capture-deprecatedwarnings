#!/usr/bin/python
# encoding: utf-8

from setuptools import setup


setup(name="pytest-capture-deprecatedwarnings",
      version='0.5.1',
      author='Laurent Peuch',
      author_email='cortex@worlddomination.be',
      url='https://github.com/psycojoker/pytest-capture-deprecatedwarnings',
      description='pytest plugin to capture all deprecatedwarnings and put them in one file',
      long_description=open("README.md").read(),
      long_description_content_type='text/markdown',
      license="MIT",
      packages=['pytest_capture_deprecatedwarnings'],
      entry_points={'pytest11': ['pytest_capture_deprecatedwarnings = pytest_capture_deprecatedwarnings']},
      install_requires=['pytest', 'importlib_metadata>=6.0.0,<7.0.0'],
      )
