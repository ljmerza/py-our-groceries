from setuptools import setup, find_packages


PACKAGES = find_packages(exclude=['tests', 'tests.*'])

REQUIRES = [
    'aiohttp==3.5.4',
    'lxml==4.3.4',
    'beautifulsoup4==4.7.1'
]

setup(
    name='py-our-groceries',  
    version='0.17',
    author="Leonardo Merza",
    author_email="ljmerza@gmail.com",
    keywords='unoffical our groceries api',
    description="Our Groceries Unofficial Python Pacakge",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ljmerza/py-our-groceries",
    license='MIT',
    packages=PACKAGES,
    include_package_data=True,
    python_requires='>=3',
    zip_safe=False,
    install_requires=REQUIRES,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
 )