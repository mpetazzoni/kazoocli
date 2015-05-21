#!/usr/bin/env python

# Copyright (C) 2015 Maxime Petazzoni <maxime.petazzoni@bulix.org>

from kazoocli.version import name, version, description
from setuptools import setup, find_packages

with open('README.md') as readme:
    long_description = readme.read()

with open('kazoocli/version.py') as f:
    exec(f.read())

with open('requirements.txt') as f:
    requirements = [line.strip() for line in f.readlines()]

setup(
    name=name,
    version=version,
    description=description,
    long_description=long_description,
    zip_safe=True,
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],

    entry_points={
        'console_scripts': ['kz = kazoocli.__main__:main'],
        'setuptools.installation': ['eggsecutable = kazoocli.__main__:main'],
    },

    author='Maxime Petazzoni',
    author_email='maxime.petazzoni@bulix.org',
    license='Apache Software License v2.0',
    keywords='zookeeper client kazoo',
    url='https://github.com/mpetazzoni/kazoocli',
)
