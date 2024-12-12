from setuptools import setup, find_packages

setup(
    name="surveillance-server",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        line.strip()
        for line in open("requirements.txt").readlines()
    ],
    python_requires=">=3.9",
)