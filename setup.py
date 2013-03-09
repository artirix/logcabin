# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="logcabin",
    url='http://github.com/artirix/logcabin/',
    version=':versiontools:logcabin:',
    license='Apache 2.0',
    description="Logging framework for receiving and processing events from a "
    "diverse range of sources and formats, and relaying onto multiple "
    "destinations.",
    long_description=file('README.rst').read(),
    author='Barnaby Gray',
    author_email='barnaby@artirix.com',
    setup_requires=[
        'versiontools',
    ],
    install_requires=[
        'python-dateutil',
        'gevent >= 0.13.6',
    ],
    tests_require=[
        'nose',
    ],
    test_suite="nose.collector",
    packages=find_packages(exclude=('docs', 'test')),
    package_data={'logcabin': ['logging.cfg']},
    zip_safe=False,
    entry_points={
        'console_scripts':
        ['logcabin = logcabin:main']
    },
)
