""" 
Setup for the futuregrid
"""
from setuptools import setup

setup(
    name = 'futuregrid',
    version = '0.2',
    description = "FutureGrid (Python)",
    long_description = '''\
futuregrid is a python library that contains the code related dynamically provisioning images on hardware''',
    author = 'Gregor von Laszewski, Fugang Wang, Javier Diaz, Mike Lewis',
    author_email = 'laszewski@gmail.com',
    license = "Apache 2.0",
    platforms = "Linux",
    url = "http://futregrid.org",
    download_url = "TBD on svn",
    classifiers = [
        "Development Status :: 1 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache 2.0",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup"],
    keywords = "Grid, Cloud, HPC",
    package_dir = { '' : '.' },
    packages = [
        'shell', 'utils','var','etc','image'],
    install_requires = [
        'setuptools',
        'cmd2'
        ],
    scripts = [
        'fg-shell.py'
        ]
    )


