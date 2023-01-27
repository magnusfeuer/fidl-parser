#!/usr/bin/env python3
#
# (C) 2022 Magnus Feuer
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.


import setuptools

long_description="""## Franca IDL Parser
Python parser to create a parse tree from Franca IDL files."""

setuptools.setup(
    name="fidl-parse",
    version="0.0.1",
    author="Magnus Feuer",
    author_email="magnus@feuerworks.com",
    description="Franca IDL parser",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GENIVI/fidl-parser",
    packages=setuptools.find_packages(),
    install_requires=['lark'],
    scripts=["fidl_tool.py" ],
    data_files=[ 'fidl_parser/francaidl.lark'],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
