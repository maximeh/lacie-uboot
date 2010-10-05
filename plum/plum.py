#! /usr/bin/python -B
# -*- coding: utf-8 -*-

'''
plum allow you to discuss with the netconsol of u-boot.
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


import logging
from multiprocessing import Process, Value
import os
import readline 
# for history and elaborate line editing when using raw_input
# see http://docs.python.org/library/functions.html#raw_input
import socket
import struct
import sys
sys.dont_write_bytecode = True

import plum_net
import plum_lump
import plum_script

class Plum(object):
    '''
    This class represent and contains all objects
    needed by plum to perform its magic.
     '''
     
    def __init__(self):
        '''Sets some parameters'''
        
        self.iff_new_ip = ""
        self.iff_mac_dest = ""
        self.request_port = 4446
        self.response_port = 4445
        self.uboot_port = 6666
        self.lump_timeout = 120
        self.is_script = False
        self.debug = False

    def launch_cmd(self, cmd):
        '''
        send a cmd in a separate process
        '''
        
        exit_list = ['exit', 'reset']
        prompt = Value('i', 1)
        
        socket.setdefaulttimeout(60)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if cmd in exit_list:
            cmd = 'reset'
            cmd = struct.pack('!'+str(len(cmd))+'s1s', cmd, '\x0A')
            sock.sendto(cmd, (self.iff_new_ip, self.uboot_port))
            return 0
        else:
            scmd = Process(target=self.send_cmd, 
                    args=( cmd, prompt))
            scmd.start()
            scmd.join()
            if scmd.exitcode == 1:
                scmd.terminate()
                return 0
            scmd.terminate()

        sock.close()
        return 42
        
    def send_cmd( self, comd, prompt_check ):
        ''' send a command to a socket '''

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(10.0)
        sock_res = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_res.settimeout(10.0)

        try:
            sock_res.bind(('', self.uboot_port))
        except socket.error, err:
            logging.error("Couldn't be a udp server on port %d : %s",
                          self.response_port, err)
            sock_res.close()
            sys.exit(1)

        #we want to send a cmd to the nas and get the reply in ans
        #every command is completed by \n !
        cmd_mem = comd
        comd = struct.pack('!'+str(len(comd))+'s1s', comd, '\x0A')
        sock.sendto(comd, (self.iff_new_ip, self.uboot_port))
        send_ans = ""
        count_cmd = 0
        try:
            while prompt_check.value == 1:
                send_data = sock_res.recvfrom(1024)
                if send_data[1][0] == self.iff_new_ip:
                    from_source = True
                send_data = send_data[0]
                #check when prompt (Marvell>>) is available,
                # then out to the next while to input command and send them !
                if ("Marvell>> " == send_data \
                    or 'Override Env parameters? (y/n)' == send_data) \
                    and from_source:
                    if 'Override Env parameters? (y/n)' == send_data :
                        print send_data
                    send_data = ""
                    if "Unknown" and "command" in send_ans.split(' '):
                        logging.error("Unknown command sent to U-Boot : %s",
                                      cmd_mem)
                        prompt_check.value = 0
                        sys.exit(1)
                    prompt_check.value = 0
                elif from_source:
                    if count_cmd < len(comd):
                        count_cmd += 1
                    else:
                        # to handle the printenv and other case 
                        # when answer is given one letter at a time...
                        write = sys.stdout.write
                        write(str(send_data))
                        sys.stdout.flush()
                    send_ans += send_data
        except (socket.error, KeyboardInterrupt) as err:
            if self.debug :
                logging.error("Sending command %s on %d : %s"
                              , cmd_mem, self.response_port, err)
            sock.close()
            sock_res.close()
            sys.exit(1)

def main():
    ''' launch everything '''
   
    import optparse

    usage = "Usage: %prog [options]"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-m", "--mac", dest="mac", action="store",
                      default=None, 
                      help="Address MAC of the targeted device " \
                      "(00:00:00:00:00:00)"
                      )
    parser.add_option("-i", "--ip", dest="ip_address", action="store",
                      default=None,
                      help="Address IP of the targeted device (Mandatory)\n" \
                      " (W.X.Y.Z where 0 > W, X, Y, Z < 255)"
                      )
    parser.add_option("-p", "--progress", dest="progress", action="store_const",
                      const=True, help="Print a progess bar," \
                      " use with a script shebang only.")
    parser.add_option("-D", "--debug", dest="loglevel", action="store_const",
                      const=logging.DEBUG, help="Output debugging information")

    plum_session = Plum()
     
    if '-D' in sys.argv or \
       '--debug' in sys.argv:
        plum_session.debug = True
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    options, _ = parser.parse_args()
    if (options.mac is None or \
        options.ip_address is None ) and \
        ( len(sys.argv) == 1):
        logging.info("You should at least set theses options : ")
        logging.info(" - MAC adress (00:00:00:00:00)")
        logging.info(" - IP address (W.X.Y.Z)")
        parser.print_help()
        return 1
    elif os.path.isfile(sys.argv[len(sys.argv)-1]):
        plum_session.is_script = True
        plum_script.set_setup(plum_session, sys.argv[len(sys.argv)-1])
    else:
        plum_session.iff_mac_dest = options.mac
        plum_session.iff_new_ip = options.ip_address

    if not plum_net.is_valid_mac(plum_session.iff_mac_dest):
        logging.error("Your MAC address is not in the proper format. \
                       \'00:00:00:00:00:00\' format is awaited.")
        return 1
    if not plum_net.is_valid_ipv4(plum_session.iff_new_ip):
        logging.error("Your IP is not in the proper format. \
                      \'W.X.Y.Z\' format is awaited.")
        return 1
        
    if not plum_lump.send_lump(plum_session):
        logging.debug("LUMP was not sent/receveid by the target")

    if plum_session.is_script:
        plum_script.execute(plum_session, sys.argv[len(sys.argv)-1], options.progress)
    else:
        exit_code = 42
        while(exit_code):
            exit_code = plum_session.launch_cmd(raw_input("Marvell>> "))

    return 0

if __name__ == '__main__' :
    if sys.platform != "win32" :
        if os.geteuid() != 0:
            print "You must be administrator/root to run this program."
            sys.exit(1)

    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
    except TypeError:
        sys.stderr.write('What are you doing ? Read the manual please.\n')
        sys.stderr.flush()
        sys.exit(0)
