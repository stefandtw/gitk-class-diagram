
from setuptools import setup

version = "1.0.0"

setup(
    name="gitk-class-diagram",
    version=version,
    license="GPLv3+",
    description="Class diagrams based on commit diffs",
    url="https://github.com/stefandtw/gitk-class-diagram",
    packages=["classdiff"],
    scripts=["gitk-cl"],
    entry_points={
        "console_scripts": [
            "classdiff = classdiff.main:main",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Tcl",
        "Topic :: Software Development",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: GNU General Public License v3 or later"
        " (GPLv3+)"
    ],
)
