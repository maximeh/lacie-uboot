#! /usr/bin/python -B
# -*- coding: utf-8 -*-

'''
plum_script implement methods to read and execute a plum script
'''

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

import time
import sys


class ProgressBar:

    def __init__(self, size):
        self.percent_total = size
        self.prog_bar = '[]'
        self.fill_char = '#'
        self.width = 40
        self.__update_amount(0)

    def __update_amount(self, new_amount):
        percent_done = int(round((new_amount / 100.0) * 100.0))
        all_full = self.width - 2
        num_hashes = int(round((percent_done / 100.0) * all_full))
        self.prog_bar = '[' + self.fill_char * num_hashes + \
                        ' ' * (all_full - num_hashes) + ']'
        pct_place = (len(self.prog_bar) / 2) - len(str(percent_done))
        pct_string = '%i%%' % percent_done
        self.prog_bar = self.prog_bar[0:pct_place] + \
            (pct_string + self.prog_bar[pct_place + len(pct_string):])

    def update_percent(self, percent):
        self.__update_amount((percent / float(self.percent_total)) * 100.0)

    def __str__(self):
        return str(self.prog_bar)


def execute(session, file_path, progress):
    '''
    Read a script file and
    parse it to launch every command.
    If progress is asked, then no display.
    '''

    script_file = open(file_path, 'r+')

    script = []
    for i in script_file.readlines():
        if not (i == '\n' or i.startswith('#')):
            script.append(i.strip())
    script_file.close()

    if progress:
        progess = ProgressBar(100)
        progess.fill_char = '='
        progess.update_percent(0)

    pas = 100 / len(script)
    for line in script:
        if progress:
            progess.update_percent(pas * script.index(line))
            sys.stdout.write(str(progess) + '\r')
            sys.stdout.flush()
        else:
            print line
        session.invoke(line, not progress)
        time.sleep(1)
        #it seems uboot doesn't like being shaked a bit

    if progress:
        progess.update_percent(100)
        sys.stdout.write(str(progess) + '\r')
        sys.stdout.flush()
        print
