# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="logcabin",
    version=':versiontools:logcabin:',
    license=license,
    description="Logging framework for receiving and processing events from a "
    "diverse range of sources and formats, and relaying onto multiple "
    "destinations.",
    long_description=file('README.md').read(),
    author='Barnaby Gray',
    author_email='barnaby@artirix.com',
    setup_requires=[
        'versiontools',
    ],
    install_requires=[
        'python-dateutil',
        'pyyaml',
        'gevent >= 0.13.6',
        'pyzmq == 2.2.0.1',
        # tie to version otherwise pip insists on updating it
    ],
    tests_require=[
        'nose',
    ],
    test_suite="nose.collector",
    packages=find_packages(exclude=('docs', 'test')),
    package_data={'logcabin': ['logging.yml']},
    zip_safe=False,
    entry_points={
        'console_scripts':
        ['logcabin = logcabin:main']
    },
)
