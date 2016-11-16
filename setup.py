#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'numpy',
    'pandas',
    'h5py',
    'requests',
    'feather-format',
    'biopython',
    'click',
]

test_requirements = [
    'numpy',
    'pandas',
    'h5py',
    'requests',
    'feather-format',
    'Click',
    'pytest',
]

setup(
    name='porekit-python',
    version='0.1.0',
    description="A kit of tools for handling data from Oxford Nanopore Technologies' sequencers.",
    long_description=readme + '\n\n' + history,
    author="Andreas Klostermann",
    author_email='andreasklostermann@gmail.com',
    url='https://github.com/akloster/porekit-python',
    packages=[
        'porekit',
    ],
    package_dir={'porekit':
                 'porekit'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='porekit, oxford, nanopore, minion',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
    ],
    entry_points='''
        [console_scripts]
        porekit=porekit.scripts.main:main
    ''',
    test_suite='tests',
    tests_require=test_requirements
)
