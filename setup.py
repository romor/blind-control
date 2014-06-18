#!/usr/bin/env python3
"""This is the setup file for package creation and installation."""
import setuptools
import os
import sys
import pkg_resources


# needed packages
REQUIRES = [
    'ephem',
]


def run_setup(args):
    """install and run post-install commands."""
    # install
    setuptools.setup(
        name='rolloctrl',
        version="0.1",
        description='rolloctrl',
        long_description='control somfy rollos using weather data from ZAMG',
        author='Roman',
        author_email='maemo@morawek.at',
        packages=setuptools.find_packages(),
        include_package_data=True,
        zip_safe=False,
        install_requires=REQUIRES,
        script_name = 'setup.py',
        script_args = args,
    )


# check for execution
if __name__ == "__main__":
    run_setup(sys.argv[1:])
