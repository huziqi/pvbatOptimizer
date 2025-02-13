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
    author="Your Name",
    author_email="your.email@example.com",
    description="一个用于优化PV-储能系统容量的包",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
)