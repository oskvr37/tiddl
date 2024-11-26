from setuptools import setup, find_packages

setup(
    name="tiddl",
    version="1.8.2",
    description="TIDDL (Tidal Downloader) is a Python CLI application that allows downloading Tidal tracks.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    readme="README.md",
    author="oskvr37",
    packages=find_packages(),
    entry_points={
        "console_scripts": ["tiddl=tiddl:main"],
    },
)
