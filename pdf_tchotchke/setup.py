'''
Setup for pdf_tchotchke

Based on:
https://github.com/pypa/sampleproject
'''

from os.path import abspath, dirname
from setuptools import setup, find_packages

# Import description from README
long_description = open(dirname(abspath(__file__))+'/README.md','r').read()

setup(
    name='pdf_tchotchke',
    version='0',
    description='PDF bookmark and redaction tools',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/lord-zo/misc/',
    author='Lorenzo X. Van Muñoz',
    license='MIT',
    classifiers=[
        'Development Status :: 2 - Alpha',
        'Intended Audience :: Students',
        'Topic :: PDF editing',
        'License :: OSI Approced :: MIT License',
        'Programming Language :: Python :: 3 :: Only'
    ],
    keywords='pdf, bookmarks, redaction',
    package_dir={'': 'src'},
    packages=find_packages(
        where='src', 
        include=['bookmarks', 'utils', 'redaction']),
    install_requires=['pdfrw'],
    python_requires='~=3.9',
    entry_points={
        'console_scripts': [
            'bkmk=bookmarks:main_bkmk',
            'interleave=bookmarks:main_interleave',
            'redact=redaction:main_redact',
            'whiteout=redaction:main_whiteout'
            ],
        }
)
