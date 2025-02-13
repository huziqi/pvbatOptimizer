from setuptools import setup, find_packages

setup(
    name="pvbat_optimizer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas>=1.0.0",
        "numpy>=1.18.0",
        "gurobipy>=9.0.0",
    ],
    author="huziqi",
    author_email="ziqihu@outlook.com",
    description="A package for optimizing PV-battery system capacity",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)