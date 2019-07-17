import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='pyourgroceries',  
    version='0.1',
    scripts=['test'] ,
    author="Leonardo Merza",
    author_email="ljmerza@gmail.com",
    description="Our Groceries Unofficial Python Pacakge",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ljmerza/py-our-groceries",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
 )