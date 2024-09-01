#!/usr/bin/env python

import setuptools

# VERSION MUST be defined on line 6
VERSION = "0.16"

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="coco-tools",
    version=VERSION,
    description="TRS-80 Color Computer Tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # The project's main homepage.
    url="https://github.com/jamieleecho/coco-tools",
    # Author details
    author="Jamie Cho",
    author_email="jamieleecho+coco_tools@gmail.com",
    # Choose your license
    license="GPLv2",
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: MIT License",
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3",
    ],
    install_requires=[
        "parsimonious>=0.10.0",
        "Pillow>=7.0.0",
        "pypng>=0.0.18",
    ],
    python_requires=">=3.9.19",
    # What does your project relate to?
    keywords="coco image conversion trs-80 tandy",
    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=setuptools.find_packages(".", exclude=["tests.coco_tests"]),
    package_dir={
        "": ".",
    },
    package_data={
        "coco.resources": ["*.b09"],
    },
    entry_points={
        "console_scripts": [
            "decb-to-b09=coco.decb_to_b09:main",
            "cm3toppm=coco.cm3toppm:main",
            "hrstoppm=coco.hrstoppm:main",
            "maxtoppm=coco.maxtoppm:main",
            "mgetoppm=coco.mgetoppm:main",
            "mge_viewer2=coco.mge_viewer2:main",
            "pixtopgm=coco.pixtopgm:main",
            "rattoppm=coco.rattoppm:main",
            "veftopng=coco.veftopng:main",
        ],
    },
)
