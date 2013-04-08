#!/usr/bin/python
# -*- coding: utf-8 -*-

# Author:     Maxime Hadjinlian (C) 2013
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
import distutils
from distutils.core import setup

VERSION = '1.0'

setup(
    name='lacie_uboot',
    version=VERSION,
    packages=['lacie_uboot'],
    scripts=['bin/lacie-uboot-shell', 'bin/lacie-nas-updater'],
    data_files=[
                  ('share/man/man1', ['doc/lacie-uboot-shell.1']),
                  ('share/man/man1', ['doc/lacie-nas-updater.1']),
                 ],
    author='Maxime Hadjinlian',
    author_email='maxime.hadjinlian@gmail.com',

    maintainer='Maxime Hadjinlian',
    maintainer_email='maxime.hadjinlian@gmail.com',

    description='Access a LaCie NAS\'s U-Boot netconsole without any hardware',
    long_description='''
 LaCie Network-Attached Storage products offer a U-Boot netconsole,
 which can be accessed using the tools provided in this package:
  * lacie-uboot-shell - a simple interactive client which can connect
    to the U-Boot netconsole using only a network cable;
  * lacie-nas-updater - a script to update the device's bootloader or
    firmware using lacie-uboot-shell (requires a TFTP server).
''',
    url='http://f00.fr',

    license='GPL',

    keywords='lacie_uboot uboot lacie netconsole',
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
