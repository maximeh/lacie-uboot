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
import os
import readline
# for history and elaborate line editing when using raw_input
# see http://docs.python.org/library/functions.html#raw_input
import select
import socket
import struct
import sys
sys.dont_write_bytecode = True
import time

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
        self.broadcast_address = ""
        self.iff_mac_dest = ""
        self.request_port = 4446
        self.response_port = 4445
        self.uboot_port = 6666
        self.lump_timeout = 120
        self.is_script = False
        self.debug = False

    def invoke(self, cmd, display=True):
        '''
        send a cmd in a separate process
        '''

        # Empty command, nothing to do here
        if cmd == "":
            return 42

        exit_list = ['exit', 'reset']
        socket.setdefaulttimeout(60)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if cmd in exit_list:
            cmd = 'reset'
            cmd = struct.pack('!' + str(len(cmd)) + 's1s', cmd, '\x0A')
            sock.sendto(cmd, (self.iff_new_ip, self.uboot_port))
            sock.close()
            return 0

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(10.0)

        try:
            sock.bind(('', self.uboot_port))
        except socket.error, err:
            logging.error("Can't open %d port. (Error : %s)",
                          self.response_port, err)
            sock.close()
            return 0

        #we want to send a cmd to the nas and get the reply in ans
        #every command is completed by \n !
        command = struct.pack('!' + str(len(cmd)) + 's1s', cmd, '\x0A')
        sock.sendto(command, (self.iff_new_ip, self.uboot_port))
        prompt = False
        len_command = 0

        while prompt is False:
            srecv = select.select([sock], [], [], 0.5)
            # data
            if srecv[0]:
                try:
                    data = sock.recvfrom(1024)
                    if data[1][0] != self.iff_new_ip:
                        continue
                    recv_data = data[0]
                    # check when prompt (Marvell>>) is available,
                    if ("Marvell>> " == recv_data \
                        or 'Override Env parameters? (y/n)' == recv_data):
                        if 'Override Env parameters? (y/n)' == recv_data:
                            print recv_data
                        prompt = True
                    # When sending a command U-Boot return the commands
                    # char by char, we do this so we don't display it.
                    elif len_command < len(command):
                        len_command += 1
                        continue
                    else:
                        # to handle the printenv and other case
                        # when answer is given one letter at a time...
                        if display:
                            write = sys.stdout.write
                            write(str(recv_data))
                            sys.stdout.flush()
                except (socket.error, KeyboardInterrupt, SystemExit) as err:
                    if self.debug:
                        logging.error("Sending command %s on %d : %s",
                              cmd, self.response_port, err)
        sock.close()
        return 42


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
    parser.add_option("-i", "--iface", dest="iface", action="store",
                      default="eth0",
                      help="Interface to use to send LUMP packet to.\n"
                      "Default is eth0.\n"
                      )
    parser.add_option("", "--ip", dest="force_ip", action="store",
                      default=None,
                      help="Force the IP address if you don't want plum, " \
                      "finding a free IP on your subnet for you."
                      )
    parser.add_option("-p", "--progress", dest="progress",
                      action="store_const", default=False, const=True,
                      help="Print a pretty progess bar," \
                      " use with a script shebang only.")
    parser.add_option("-w", "--wait", dest="wait", action="store_const",
                      default=False, const=True,
                      help="Wait for the product to boot.\n" \
                      "Note : Require the -m/--mac option to be set.\n")
    parser.add_option("-D", "--debug", dest="loglevel", action="store_const",
                      const=logging.DEBUG, help="Output debugging information")

    plum_session = Plum()

    if '-D' in sys.argv or '--debug' in sys.argv:
        plum_session.debug = True
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    options, _ = parser.parse_args()
    plum_session.iff_mac_dest = options.mac

    if options.mac is None:
        logging.info("WARNING : The first product to reboot will be catched !")
        logging.info("It may not be yours if multiple product reboot at the "
                     "same time on your network.")
        plum_session.iff_mac_dest = "00:00:00:00:00:00"

    if len(sys.argv) >= 2 and os.path.isfile(sys.argv[1]):
        plum_session.is_script = True

    try:
        ip, mac, netmask, bcast = plum_net.get_iface_info(options.iface)
    except IOError:
        logging.error("Your network interface is not reachable." +
                      " Is %s correct ?", options.iface)
        return 1

    plum_session.broadcast_address = bcast
    # This IP is used afterwards when TFTP'ing files
    if options.force_ip is not None:
        plum_session.iff_new_ip = options.force_ip
    else:
        plum_session.iff_new_ip = plum_net.find_free_ip(options.iface,
                                                    ip, mac, netmask)

    # Check MAC and IP value.
    if not plum_net.is_valid_mac(plum_session.iff_mac_dest):
        logging.error("Your MAC address is not in the proper format." +
                      "\'00:00:00:00:00:00\' format is awaited. Given %s" \
                              % plum_session.iff_mac_dest)
        return 1
    if not plum_net.is_valid_ipv4(plum_session.broadcast_address):
        logging.error("Your Broadcast IP is not in the proper format." +
                      "\'W.X.Y.Z\' format is awaited. Given %s" \
                      % plum_session.broadcast_address)
        return 1
    if not plum_net.is_valid_ipv4(plum_session.iff_new_ip):
        logging.error("Your product IP is not in the proper format." +
                      "\'W.X.Y.Z\' format is awaited. Given %s" \
                      % plum_session.iff_new_ip)
        return 1

    if not plum_lump.lump(plum_session):
        logging.debug("LUMP was not sent/receveid by the target")

    if plum_session.is_script:
        plum_script.execute(plum_session, sys.argv[1], options.progress)
        # You can't wait if there is no MAC.
        if options.wait and (plum_session.iff_mac_dest != "00:00:00:00:00:00"):
            # WAIT FOR THE DEVICE TO BOOT
            logging.info("Waiting for your product to reboot...")
            time.sleep(60 * 7)  # Wait 7mn for the product to apply capsule
            ip = plum_lump.get_ipcomm_info(plum_session)
            if ip is not None:
                logging.info("Your product is available at %s" % ip)
            else:
                logging.info("Timeout : Unable to get your product IP.")
        return 0

    exit_code = 42
    while(exit_code):
        exit_code = plum_session.invoke(raw_input("Marvell>> "),
                                            not options.progress)

    return 0

if __name__ == '__main__':
    if sys.platform != "win32":
        if os.geteuid() != 0:
            print "You must be administrator/root to run this program."
            sys.exit(1)

    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError, SystemExit, KeyError):
        pass
