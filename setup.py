#!/usr/bin/env python

#
# see also http://mrtopf.de/blog/en/a-small-introduction-to-python-eggs/
#

from distutils.core import setup

setup(
    name='eventlet',
    version='0.1',
    description='FutureGrid library',
    author='The FutureGrid Team',
    author_email='laszewski@gmail.com',
    url='https://portal.futuregrid.org/software',
    packages=['futuregrid'])
      long_description="""\
      futuregrid is a python library that contains the code related dynamically provisioning images on hardware ...
      """,
      classifiers=[
          "License :: OSI Approved :: Apache 2.0",
          "Programming Language :: Python",
          "Development Status :: 0 - Alpha ",
          "Intended Audience :: Developers",
          "Topic :: Cloud and Grid",
      ],
      keywords='cloud grid',
      license='Apache',
      install_requires=[
        'setuptools',
        'greenlet'
      ],
