#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021  The SymbiFlow Authors.
#
# Use of this source code is governed by a ISC-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/ISC
#
# SPDX-License-Identifier: ISC


import setuptools


# Generate the version number
def get_version():
    def clean_scheme(version):
        from setuptools_scm.version import get_local_node_and_date
        return get_local_node_and_date(version) if version.dirty else ''

    return {
        'write_to': 'sdf_timing/version.py',
        'version_scheme': 'post-release',
        'local_scheme': clean_scheme,
    }


# Read in the module description from the README.md file.
with open("README.md", "r") as fh:
    long_description = fh.read()


# Read in the setup_requires from the requirements.txt file.
setup_requires = []
with open('requirements.txt') as fh:
    for r in fh:
        if '#' in r:
            r = r[:r.find('#')]
        r = r.strip()
        if not r:
            continue
        if r not in ('-e .',):
            setup_requires.append(r)


setuptools.setup(
    # Package human readable information
    name="sdf_timing",
    use_scm_version=get_version(),
    author="SymbiFlow Authors",
    author_email="symbiflow@lists.librecores.org",
    description="Python library for working Standard Delay Format \
                (SDF) Timing Annotation files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SymbiFlow/python-sdf-timing",
    license="ISC",
    license_files=["LICENSE"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: OS Independent",
    ],
    # Package contents control
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': ['sdf_timing_parse=sdf_timing.sdfparse:main'],
    },
    # Requirements
    python_requires=">=3.6",
    setup_requires=setup_requires,
    install_requires=[
        'ply',
        'pyjson',
    ],
    tests_require=[
        "pytest",
    ],
)
