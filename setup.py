import os

from setuptools import setup, find_packages


def read(fname):
    with open(os.path.join(os.path.dirname(__file__), fname)) as f:
        return f.read()


setup(
    name='pybradesco',
    version='0.0.0',
    url='https://github.com/andreroggeri/pybradesco',
    author='André Roggeri Campos',
    author_email='a.roggeri.c@gmail.com',
    license='MIT',
    packages=find_packages(),
    install_requires=['playwright'],
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    classifiers=[
        'Programming Language :: Python',
    ]
)
