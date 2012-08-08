#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author:     Maxime Hadjinlian
#             maxime.hadjinlian@gmail.com
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
from distutils.core import setup
from distutils.ccompiler import new_compiler
from distutils.file_util import move_file

VERSION = 0.1


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

tftpd = new_compiler()
tftpd.set_libraries('pthread')
tftpd.compile(['opentftp/opentftpd.cpp'], output_dir='build')

# Copy the binary compiled
move_file('build/opentftp/opentftpd.o', 'build/opentftpd')

setup(
    name='plum',
    version=VERSION,
    packages=[
        'plum',
    ],
    #ext_modules=[tftpd],
    scripts=['bin/plum', 'bin/capsup', 'build/opentftpd'],
    data_files=[('share/man/man1', ['doc/plum.1']),
                ('etc/', ['opentftp/opentftp.ini'])],
    author='Maxime Hadjinlian',
    author_email='maxime.hadjinlian@gmail.com',

    maintainer='Maxime Hadjinlian',
    maintainer_email='maxime.hadjinlian@gmail.com',

    description='Python LaCie das U-Boot Milchkuh',
    long_description=read('README.md'),
    url='http://f00.fr',

    license='GPL',

    keywords='plum uboot lacie netconsole',
    classifiers=[
        "Topic :: Utilities",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: System :: Shells",
        "Topic :: Terminals :: Terminal Emulators/X Terminals",
    ],
)
