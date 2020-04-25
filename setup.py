import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='pypi-metadata-analyser',
    version='1.0.0',
    author='Chris Brookes',
    author_email='chris-brookes93@outlook.com',
    description='Downloads and processes PyPi package metadata into an SQLite database for easy querying',
    long_description=long_description,
    long_description_content_type='text/markdown',
    download_url="<TODO>",
    url='<TODO>',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'six',
        'sqlite3worker',
        'lxml',
        'requests'
    ]
)
