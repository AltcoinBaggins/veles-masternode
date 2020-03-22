import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="veles-masternode",
    version="1.99.2",
    author="Veles Core",
    author_email="admin@veles.network",
    description="Veles Core Masternode",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/velescore/veles-masternode",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)