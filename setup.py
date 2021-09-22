from setuptools import setup, find_packages

PACKAGES = find_packages(exclude=['tests', 'tests.*'])

REQUIRES = [
    'aiohttp==3.6.1',
    'beautifulsoup4==4.7.1'
]

setup(
    name='ourgroceries',
    version='1.3.9',
    author="Leonardo Merza",
    author_email="ljmerza@gmail.com",
    keywords='unoffical our groceries api',
    description="Our Groceries Unofficial Python Package",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ljmerza/py-our-groceries",
    license='MIT',
    packages=PACKAGES,
    include_package_data=True,
    python_requires='>=3.5',
    zip_safe=False,
    install_requires=REQUIRES,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
