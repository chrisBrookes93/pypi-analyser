import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
    name='pypi-metadata-analyser',
    version='1.0.0',
    author='Chris Brookes',
    author_email='chris-brookes93@outlook.com',
    description='Downloads PyPi package metadata into an SQLite database that can then be queried locally.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    download_url="https://github.com/chrisBrookes93/pypi-metadata-analyser/releases/download/1.0.0/pypi-metadata-analyser-1.0.0.tar.gz",
    url='https://github.com/chrisBrookes93/pypi-metadata-analyser',
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
    ],
    entry_points={
        'console_scripts': [
            'pypianalyser=pypianalyser:main'
        ]
    }
)
