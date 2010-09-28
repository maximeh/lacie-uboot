#! /usr/bin/python -B
# -*- coding: utf-8 -*-

'''
plum allow you to discuss with the netconsol of u-boot.
'''

# Author:     Maxime Hadjinlian
#             maxime.hadjinlian@gmail.com
#
# This file is part of plum.
#
# plum is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# plum is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with plum.  If not, see <http://www.gnu.org/licenses/>.

import logging
from multiprocessing import Process, Value
import os
import socket
import struct
import sys

import plum_net
import plum_lump

class Plum(object):
    '''
    This class represent and contains all objects
    needed by plum to perform its magic.
     '''
    def __init__(self, conf_file):
        '''Sets some parameters'''
        
        self.iff_new_ip = ""
        self.iff_mac_dest = ""
        self.request_port = 4446
        self.response_port = 4445
        self.uboot_port = 6666
        self.lump_timeout = 120
        self.debug = False

    def launch_server(self, prompt):
        '''
        launch the server method in a separate process
        '''
        
        try:
            serv = Process(target=self.server, args=( prompt, ))
            serv.start()
        except socket.error:
            logging.error("Sending LUMP for 60s, no Marvel prompt !")
            serv.terminate()
            sys.exit(1)   

    def server(self, prompt_check):
        ''' connect to the netconsole until answer is given back '''

        socket.setdefaulttimeout(60)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock.bind(('', self.uboot_port))
        except socket.error, err:
            logging.error("Couldn't be a udp server on port %d : %s",
                          self.uboot_port, err)
            sock.close()
            sys.exit(1)

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        from_source = False
        while prompt_check.value:
            try:
                serv_data = sock.recvfrom(1024)
                if serv_data[1][0] == self.iff_new_ip:
                    from_source = True
                serv_data = serv_data[0]
                # check when prompt (Marvell>>) is available,
                # then out to the next while to input command and send them !
                if "Marvell>> " == serv_data and from_source:
                    prompt_check.value = 0
                serv_data = ""
            except socket.error:
                pass

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
                        print send_data,
                    send_ans += send_data
        except socket.error, err:
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
                      help="Address MAC of the targeted device")
    parser.add_option("-i", "--ip", dest="ip_address", action="store",
                      default=None,
                      help="Address IP of the targeted device (Mandatory)")
    parser.add_option("-D", "--debug", dest="loglevel", action="store_const",
                      const=logging.DEBUG, help="Output debugging information")

    plum_session = Plum('plum.cfg')
 
    options, _ = parser.parse_args()
    if (options.mac is None or \
            options.ip_address is None ) :
        logging.info("You should at least set theses options : ")
        logging.info(" - MAC adress (00:00:00:00:00)")
        logging.info(" - IP address (W.X.Y.Z)")
        parser.print_help()
        sys.exit(1)

    if '-D' in sys.argv or \
       '--debug' in sys.argv:
        plum_session.debug = True
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    plum_session.iff_mac_dest = options.mac
    plum_session.iff_new_ip = options.ip_address

    if not plum_net.is_valid_mac(plum_session.iff_mac_dest):
        logging.error("Your MAC address is not in the proper format. \
                       \'00:00:00:00:00:00\' format is awaited.")
        sys.exit(1)
    if not plum_net.is_valid_ipv4(plum_session.iff_new_ip):
        logging.error("Your IP is not in the proper format. \
                      \'W.X.Y.Z\' format is awaited.")
        sys.exit(1)
    
    
    # prompt is a shared value to stop both client
    # and server when "Marvell>> " is received.
    prompt = Value('i', 1)
        
    plum_session.launch_server(prompt) 
        
    if not plum_lump.send_lump(plum_session, prompt):
        logging.debug("LUMP was not sent/receveid by the target")

    exit_code = 42
    while(exit_code):
        exit_code = plum_session.launch_cmd(raw_input("Marvell>> "))

    sys.exit(0)

if __name__ == '__main__' :
    if sys.platform != "win32" :
        if os.geteuid() != 0:
            print "You must be administrator/root to run this program."
            sys.exit(1)
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

