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
import select
import socket
import struct
import sys
from time import clock, sleep

sys.dont_write_bytecode = True

# Define IFF type used in the LUMP packet
IFF_LUMP_TYPE = 0x4C554D50
IFF_IP_TYPE   = 0x49504000
IFF_IPS_TYPE  = 0x49505300
IFF_MAC_TYPE  = 0x4D414340
IFF_MACD_TYPE = 0x4D414344
IFF_MACS_TYPE = 0x4D414353


def lump(session):
    '''
    It will ask the users to reboot the target manually and then
    it will send LUMP packet to a target during 60s.
    '''

    # Create an array with 6 cases, each one is a member (int) of the MAC
    fields_macdest = [int(x, 16) for x in session.iff_mac_dest.split(':')]

    # Create an array with 4 cases, each one is a member (int) of the IP
    fields_ip = [int(x) for x in session.iff_new_ip.split('.')]

    # Note : The empty MAC are 8 bytes in length according to the reverse
    # engineering done with WireShark. Don't know why exactly...
    pkt = struct.pack('!I'   # LUMP
                      'L'    # Length of LUMP
                      'I'    # MACD
                      'L'    # Length of MACD
                      'I'    # MAC@
                      'L'    # Length of MAC@ field
                      '2x'   # fill space because MAC take only 6 bytes
                      '6s'   # MAC address of target
                      'I'    # IPS
                      'L'    # Length of IPS
                      'I'    # IP@
                      'L'    # Length of IP@
                      '4s'   # IP of the target
                      'I'    # MACS
                      'L'    # Length of MACS
                      'I'    # MAC address of source
                      'L'    # Length of MAC@
                      '8x',  # Empty MAC
                      IFF_LUMP_TYPE,
                      0x44,
                      IFF_MACD_TYPE,
                      0x10,
                      IFF_MAC_TYPE,
                      0x8,
                      struct.pack('!6B', *fields_macdest),  # int[] -> byte[]
                      IFF_IPS_TYPE,
                      0x0C,
                      IFF_IP_TYPE,
                      0x4,
                      struct.pack('!4B', *fields_ip),  # int[] -> byte[]
                      IFF_MACS_TYPE,
                      0x10,
                      IFF_MAC_TYPE,
                      0x8)

    logging.debug("Sending some LUMP / Ctrl-C, "
                  "waiting for the NAS to start up")
    logging.info("Please /!\HARD/!\ reboot the device /!\NOW/!\ ")

    timeout = 0
    socket.setdefaulttimeout(60)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    try:
        sock.bind(('', session.uboot_port))
    except socket.error, err:
        logging.error("Couldn't be a udp server on port %d : %s",
                      session.uboot_port, err)
        sock.close()
        return None

    lump_ok = False
    while lump_ok is False and timeout < session.lump_timeout:
        sock.sendto(pkt, (session.broadcast_address, session.request_port))
        sleep(0.2)  # Wait for the device to process the LUMP
        #Send Ctrl-C (Code ASCII 3 for EXT equivalent of SIGINT for Unix)
        sock.sendto('\3', (session.broadcast_address, session.uboot_port))
        srecv = select.select([sock], [], [], 1)
        # data
        if srecv[0]:
            try:
                serv_data = sock.recvfrom(1024)
                if serv_data[1][0] != session.iff_new_ip:
                    continue
                serv_data = serv_data[0]
                # check when prompt (Marvell>>) is available,
                # then out to the next while to input command and send them !
                if "Marvell>> " == serv_data:
                    lump_ok = True
                    break
            except (socket.error, KeyboardInterrupt, SystemExit):
                return None
        timeout += 1

    if timeout >= session.lump_timeout:
        logging.debug("Sending LUMP for %ds, no response !",
                       session.lump_timeout)
        lump_ok = False

    sock.close()
    return lump_ok


def tlvs(data):
    '''TLVs parser generator'''
    dict_data = {}
    while data:
        typ, length = struct.unpack('!4sL', data[:8])
        value = struct.unpack('!%is' % length, data[8:8 + length])[0]
        if typ == "INTF" or typ == "IPV4":
            data = data[8:]  # Skip INTF header
            continue
        dict_data[typ.rstrip(' \t\r\n\0')] = value.rstrip(' \t\r\n\0')
        data = data[8 + length:]
    return dict_data


def get_ipcomm_info(session):
    '''
    This function will send LOOK packet to a target
    Then will parse the INFO packet and return the first found ip.
    '''
    ip = None
    pkt = struct.pack('!4s14x', "\x4c\x4f\x4f\x4b")  # LOOK (at the ring !)

    socket.setdefaulttimeout(60)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setblocking(0)

    # Listen for the answer
    try:
        sock.bind(('', session.response_port))
    except socket.error, err:
        print("Couldn't be a udp server on port %d : %s",
                      session.response_port, err)
        sock.close()
        return None

    ip = None
    tryout = 0  # Number of tries, don't want to stay here forever
    while ip is None and tryout < 10:
        sock.sendto(pkt, ('255.255.255.255', session.response_port))
        stop = clock() + 0.05
        while stop > clock() and ip is None:
            try:
                serv_data = sock.recv(1024)
            except:
                continue
            if len(serv_data) <= 8:
                continue
            info = struct.unpack('!4s', serv_data[:4])
            if info[0] != "INFO":
                continue
            data = tlvs(serv_data[8:])  # strip info header
            if data["MAC"].lower() == session.iff_mac_dest.lower():
                if data["ADDR"].lower() == session.iff_new_ip.lower():
                    continue
                ip = data["ADDR"]
        tryout += 1
    return ip
