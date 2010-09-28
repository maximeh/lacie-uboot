#! /usr/bin/python -B
# -*- coding: utf-8 -*-

'''
plum_lump send a lump to a target followed by a CTRL+C to catch the netconsole.
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
import socket
import struct
import time

# Define IFF type used in the LUMP packet
IFF_LUMP_TYPE = 0x4C554D50
IFF_IP_TYPE   = 0x49504000
IFF_IPS_TYPE  = 0x49505300
IFF_MAC_TYPE  = 0x4D414340
IFF_MACD_TYPE = 0x4D414344
IFF_MACS_TYPE = 0x4D414353
IFF_MAC_ANY = "00:00:00:00:00:00"

def send_lump(session, prompt):
    '''
    This function will send LUMP packet to a target during 60s
    Then will ask the users to reboot the target manually.
    '''

    lump_ok = True
    #Pack a MAC address (00:00:00:00:00:00) into a 6 byte string.
    fields_macdest = [int(x, 16) for x in session.iff_mac_dest.split(':')]
    fields_macany = [int(x, 16) for x in IFF_MAC_ANY.split(':')]

    #Pack an IP address (192.168.8.115) into a 4 byte string.
    fields_ip = [int(x) for x in session.iff_new_ip.split('.')]

    fmt = '!6I1s1s6B4I4B4I1s1s6B'
    # We pack the LUMP packet as it should be.
    pkt = struct.pack(fmt, 
    IFF_LUMP_TYPE, 0x44, IFF_MACD_TYPE, 0x10, IFF_MAC_TYPE, 0x8,
    '\x00', '\x00', fields_macdest[0], fields_macdest[1], fields_macdest[2],
    fields_macdest[3], fields_macdest[4], fields_macdest[5],
    IFF_IPS_TYPE, 0x0C, IFF_IP_TYPE, 0x4, 
    fields_ip[0], fields_ip[1], fields_ip[2], fields_ip[3],
    IFF_MACS_TYPE, 0x10, IFF_MAC_TYPE, 0x08, '\x00','\x00',
    fields_macany[0], fields_macany[1], fields_macany[2], fields_macany[3],
    fields_macany[4], fields_macany[5])

    logging.debug("Sending some LUMP / Ctrl-C, waiting for the NAS to start up")
    logging.info("Please /!\HARD/!\ reboot the device /!\NOW/!\ ")

    timeout = 0
    socket.setdefaulttimeout(60)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    while prompt.value and timeout < session.lump_timeout:
        sock.sendto(pkt, ('255.255.255.255', session.request_port))
        time.sleep(0.2) #Wait for the device to process the LUMP
        #Send Ctrl-C (Code ASCII 3 for EXT equivalent of SIGINT for Unix)
        sock.sendto('\3', ('255.255.255.255', session.uboot_port))

        time.sleep(1)
        timeout += 1

    if timeout >= session.lump_timeout:
        logging.debug("Sending LUMP for %ds, no response !",
                       session.lump_timeout)
        sock.close()
        lump_ok = False

    return lump_ok
    
