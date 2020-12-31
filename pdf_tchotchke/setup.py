#!/usr/bin/env python3
'''
Setup for pdf_tchotchke

Based on:
https://github.com/pypa/sampleproject
'''

from setuptools import setup, find_packages

setup(
    name='pdf_tchotchke',
    version='0.0',
    description='PDF bookmark and redaction tools',
    long_description=open('./README.md','r').read(),
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
    packages=find_packages(),
    requires=['pdftotext'],
    python_requires='>=3.7.3',
    entry_points={
        'console_scripts': [
            'bkmk=pdf_tchotchke.bookmarks.bkmk:cli',
            'interleave=pdf_tchotchke.bookmarks.interleave:cli',
            'redact=pdf_tchotchke.redaction.redact:cli',
            'whiteout=pdf_tchotchke.redaction.whiteout:cli',
            'prepare=pdf_tchotchke.redaction.prepare:cli',
            ]
        }
)
