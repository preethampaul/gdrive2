# -*- coding: utf-8 -*-

import setuptools
from gdrive.paths import VERSION

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gdrive",
    version=VERSION,
    author="Preetham Paul",
    author_email="preeth@uw.edu",
    description="File management tools for Google Drive based on PyDrive",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/preethampaul/gdrive",
    project_urls={
    	"Documentation" : "https://gdrive.readthedocs.io"
    },
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3',

    package_data={
    "" : ["gd"],
    },
    install_requires=[
        'PyDrive>=1.3.1'
    ]
)