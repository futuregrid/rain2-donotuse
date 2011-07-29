""" 
Note: All of the capitalized constants below are passed to the distutils
  setup() function you see below in the __main__ block [Python's main()].

Everything is contained in src, which itself is not part of the package 
structure. The only package (at present) is 'cogkit'. Others could be created
and added to the PACKAGES variable below.

This configuration file is modified and its origin is in cogkit.org and cyberaide.org
"""

from setuptools import setup

NAME = 'futuregrid'
SOURCE = '.'
PACKAGES = ['shell', 'utils','var','etc','image']
VERSION = '0.2'
DESCRIPTION = "FutureGrid (Python)"
LONG_DESCRIPTION = """\
futuregrid is a python library that contains the code related dynamically provisioning images on hardware ...

"""
AUTHOR ="Gregor von Laszewski, Fugang Wang, Javier Diaz, Mike Lewis"
AUTHOR_EMAIL = 'laszewski@gmail.com'
LICENSE = "Apache 2.0"
PLATFORMS = "Linux"
URL = "http://futregrid.org"
DOWNLOAD_URL = "http://%s/download/%s-%s.tar.gz" % (URL, NAME, VERSION)
CLASSIFIERS = [
    "Development Status :: 1 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache 2.0",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Text Processing :: Markup"]
KEYWORDS = "Grid, Cloud"

from distutils.core import setup

if __name__ == '__main__':
    setup(
        name = NAME,
        version = VERSION,
        description = DESCRIPTION,
        long_description = LONG_DESCRIPTION,
        author = AUTHOR,
        author_email = AUTHOR_EMAIL,
        license = LICENSE,
        platforms = PLATFORMS,
        url = URL,
        download_url = DOWNLOAD_URL,
        classifiers = CLASSIFIERS,
        keywords = KEYWORDS,
        package_dir = { '' : SOURCE },
        packages = PACKAGES,
        install_requires = [
          'setuptools',
          'greenlet'
        ]
    )


