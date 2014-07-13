#!/usr/bin/env python3
"""This is the setup file for package creation and installation."""
import setuptools
import os
import sys
import pkg_resources


# needed packages
REQUIRES = [
    'ephem',
    'RPi.GPIO',
]


def run_setup(args):
    """install and run post-install commands."""
    # install
    setuptools.setup(
        name='blindctrl',
        version="0.1",
        description='blind-control',
        long_description='Automatically control motorized blinds depending on sun radiation and temperature using a Somfy RTS remote control and a Raspberry Pi.',
        author='Roman Morawek',
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
