from setuptools import setup, find_packages

setup(
    name='py-our-groceries',  
    version='0.16',
    author="Leonardo Merza",
    author_email="ljmerza@gmail.com",
    keywords='unoffical our groceries api',
    description="Our Groceries Unofficial Python Pacakge",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ljmerza/py-our-groceries",
    license='MIT',
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
 )