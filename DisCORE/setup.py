import setuptools

version = "0.6.3"

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="DisCORE-LDShadowLord", # Replace with your own username
    version=version,
    author="LDShadowLord",
    author_email="ldshadowlord@gmail.com",
    description="A library of scripts for manipulating data and webhooks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/LDShadowLord/DisCORE",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
