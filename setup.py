#!/usr/bin/env python
from setuptools import setup
import os

README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name = 'django-vsphere',
    version = '0.2',
    packages = ['vsphere'],
    include_package_data = True,
    description = 'Django app for vSphere Dashboard.',
    long_description = README,
    author = 'Julien Collas',
    author_email = 'jul.collas@gmail.com',
    install_requires=['django-tastypie', 'python-mimeparse'],
    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP'
    ],
)