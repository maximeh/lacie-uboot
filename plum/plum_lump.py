#! /usr/bin/python -B
# -*- coding: utf-8 -*-

'''
plum_lump send a lump to a target followed by a CTRL+C to catch the netconsole.
A server process is launched to listen while the LUMP is sent
and not hammer down the network.
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
import socket
import struct
import sys
import time

sys.dont_write_bytecode = True

# Define IFF type used in the LUMP packet
IFF_LUMP_TYPE = 0x4C554D50
IFF_IP_TYPE   = 0x49504000
IFF_IPS_TYPE  = 0x49505300
IFF_MAC_TYPE  = 0x4D414340
IFF_MACD_TYPE = 0x4D414344
IFF_MACS_TYPE = 0x4D414353

def launch_server(plum_session, prompt):
    '''
    launch the server method in a separate process
    return the process created or None.
    '''

    try:
        serv = Process(target=udp_server, \
                       args=( plum_session.iff_new_ip, \
                              plum_session.uboot_port, prompt, ))
        serv.start()
        return serv
    except (socket.error, KeyboardInterrupt):
        logging.error("Sending LUMP for 60s, no Marvel prompt !")
        serv.terminate()
        return None

def udp_server(iff_new_ip, uboot_port, prompt_check):
    ''' connect to the netconsole until answer is given back '''

    socket.setdefaulttimeout(60)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.bind(('', uboot_port))
    except socket.error, err:
        logging.error("Couldn't be a udp server on port %d : %s",
                      uboot_port, err)
        sock.close()
        return None

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    from_source = False
    while prompt_check.value:
        try:
            serv_data = sock.recvfrom(1024)
            if serv_data[1][0] == iff_new_ip:
                from_source = True
            serv_data = serv_data[0]
            # check when prompt (Marvell>>) is available,
            # then out to the next while to input command and send them !
            if "Marvell>> " == serv_data and from_source:
                prompt_check.value = 0
            serv_data = ""
        except (socket.error, KeyboardInterrupt):
            return None

def send_lump(session):
    '''
    This function will send LUMP packet to a target during 60s
    Then will ask the users to reboot the target manually.
    '''

    # Launch the server to listen while sending
    # We use a shared value to stop both client
    # and server when "Marvell>> " is received.
    # Note the space.
    prompt = Value('i', 1)
    server = launch_server(session, prompt) 

    lump_ok = True

    # Create an array with 6 cases, each one is a member (int) of the MAC 
    fields_macdest = [int(x, 16) for x in session.iff_mac_dest.split(':')]

    # Create an array with 4 cases, each one is a member (int) of the IP 
    fields_ip = [int(x) for x in session.iff_new_ip.split('.')]

    pkt = struct.pack('!I' # LUMP
                      'L'  # Length of LUMP
                      'I'  # MACD
                      'L'  # Length of MACD
                      'I'  # MAC@
                      'L'  # Length of MAC@ field
                      '2x' # fill space because MAC take only 6 bytes
                      '6s' # MAC address of target
                      'I'  # IPS
                      'L'  # Length of IPS
                      'I'  # IP@
                      'L'  # Length of IP@
                      '4s' # IP of the target
                      'I'  # MACS
                      'L'  # Length of MACS
                      'I'  # MAC address of source
                      'L'  # Length of MAC@
                      '8x',  # Empty MAC (should be 6x but according to wireshark, we need the extra)
                      IFF_LUMP_TYPE,
                      0x44,
                      IFF_MACD_TYPE,
                      0x10,
                      IFF_MAC_TYPE,
                      0x8,
                      struct.pack('!6B', *fields_macdest), # int[] -> byte[]
                      IFF_IPS_TYPE,
                      0x0C,
                      IFF_IP_TYPE,
                      0x4,
                      struct.pack('!4B', *fields_ip), # int[] -> byte[]
                      IFF_MACS_TYPE,
                      0x10,
                      IFF_MAC_TYPE,
                      0x8)

    logging.debug("Sending some LUMP / Ctrl-C, waiting for the NAS to start up")
    logging.info("Please /!\HARD/!\ reboot the device /!\NOW/!\ ")

    timeout = 0
    socket.setdefaulttimeout(60)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while prompt.value and timeout < session.lump_timeout:
        sock.sendto(pkt, (session.broadcast_address, session.request_port))
        time.sleep(0.2) #Wait for the device to process the LUMP
        #Send Ctrl-C (Code ASCII 3 for EXT equivalent of SIGINT for Unix)
        sock.sendto('\3', (session.broadcast_address, session.uboot_port))

        time.sleep(1)
        timeout += 1

    if timeout >= session.lump_timeout:
        logging.debug("Sending LUMP for %ds, no response !",
                       session.lump_timeout)
        sock.close()
        lump_ok = False

    server.terminate()
    return lump_ok

