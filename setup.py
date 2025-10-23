from setuptools import setup,find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="Celebrity Detector",
    version="0.1",
    author="Mohit",
    packages=find_packages(),
    install_requires = requirements,
)