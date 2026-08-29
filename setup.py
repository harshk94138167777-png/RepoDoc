# 100% stdlib-compatible — uses only setuptools (bundled with Python / pip)
from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="repodoctor-cli",
    version="1.0.1",
    description="Zero-dependency repository health analyser",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tanish Jain, Harsh Kumawat",
    license="MIT",
    packages=find_packages(),          # auto-discovers repodoctor/
    python_requires=">=3.8",
    install_requires=[],               # ZERO runtime dependencies
    entry_points={
        "console_scripts": [
            "repodoctor=repodoctor.__main__:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Quality Assurance",
        "Environment :: Console",
    ],
)
