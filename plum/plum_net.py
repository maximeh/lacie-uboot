#! /usr/bin/python -B
# -*- coding: utf-8 -*-

'''
plum_net is a small net library with a few utils functions.
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

import fcntl
import logging
from random import randint
import re
import select
import socket
from struct import pack
import sys
sys.dont_write_bytecode = True


def is_valid_ipv4(ip_v4):
    '''Validates IPv4 addresses.i'''
    pattern = re.compile(r"""
        ^
        (?:
          # Dotted variants:
          (?:
            # Decimal 1-255 (no leading 0's)
            [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
          |
            0x0*[0-9a-f]{1,2}  # Hexadecimal 0x0 - 0xFF (possible leading 0's)
          |
            0+[1-3]?[0-7]{0,2} # Octal 0 - 0377 (possible leading 0's)
          )
          (?:                  # Repeat 0-3 times, separated by a dot
            \.
            (?:
              [3-9]\d?|2(?:5[0-5]|[0-4]?\d)?|1\d{0,2}
            |
              0x0*[0-9a-f]{1,2}
            |
              0+[1-3]?[0-7]{0,2}
            )
          ){0,3}
        |
          0x0*[0-9a-f]{1,8}    # Hexadecimal notation, 0x0 - 0xffffffff
        |
          0+[0-3]?[0-7]{0,10}  # Octal notation, 0 - 037777777777
        |
          # Decimal notation, 1-4294967295:
          429496729[0-5]|42949672[0-8]\d|4294967[01]\d\d|429496[0-6]\d{3}|
          42949[0-5]\d{4}|4294[0-8]\d{5}|429[0-3]\d{6}|42[0-8]\d{7}|
          4[01]\d{8}|[1-3]\d{0,9}|[4-9]\d{0,8}
        )
        $
    """, re.VERBOSE | re.IGNORECASE)
    return pattern.match(ip_v4) is not None


def is_valid_mac(mac):
    ''' Validates MAC addresses separated with columns'''
    validator = '([a-fA-F0-9]{2}[:]?){6}'  # this is the regex
    return re.compile(validator).search(mac)


def get_iface_info(ifn):
    sck = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    info = fcntl.ioctl(sck.fileno(), 0x8927,  pack('256s', ifn[:15]))
    mac = ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]

    ip_str = socket.inet_ntoa(fcntl.ioctl(sck.fileno(), 0x8915,
                              pack('256s', ifn[:15]))[20:24])
    ip = [int(x) for x in ip_str.split(".")]

    netmask_str = socket.inet_ntoa(fcntl.ioctl(sck.fileno(), 0x891b,
                                   pack('256s', ifn[:15]))[20:24])
    netmask = [int(x) for x in netmask_str.split(".")]

    bcast = [0, 0, 0, 0]
    for i in range(4):
        bcast[i] = ip[i] | (~netmask[i] & 0xFF)
    bcast = ".".join([str(x) for x in bcast])

    return ip_str, mac, netmask_str, bcast


def get_random_ip_in_subnet(ip, netmask):
    netmask_bin = ''.join([bin(int(x) + 256)[3:] for x in netmask.split('.')])
    netmask_length = sum([int(x) for x in netmask_bin])

    # We can change this number of bits
    change_length = 32 - netmask_length

    not_valid = True
    while not_valid:
        # Generate random bits word of change_length
        change = "".join(str(randint(0, 1)) for i in range(change_length))
        not_valid = False
        # Check that each word is not 0 or 255, that would cause trouble
        for x in range(change_length / 8):
            word = int(change[x * 8:(x * 8) + 8], 2)
            if (word == 0) or (word == 255):
                not_valid = True
                break

    ip_bin = ''.join([bin(int(x) + 256)[3:] for x in ip.split('.')])
    ip_bin = ip_bin[:-change_length] + change
    return '.'.join((str(int(ip_bin[x * 8:(x * 8) + 8], 2)) for x in range(4)))


def prettify(mac_string):
    return ':'.join('%02x' % ord(b) for b in mac_string)


def send_arp(iface, sender_ip, sender_mac, target_ip, arptype):

    """
    Sample ARP frame
    +-----------------+------------------------+
    | Destination MAC | Source MAC             |
    +-----------------+------------------------+
    | \x08\x06 (arp)  | \x00\x01  (ethernet)   |
    +-----------------+------------------------+
    | \x08\x00 (internet protocol)             |
    +------------------------------------------+
    | \x06\x04 (hardware size & protocol size) |
    +------------------------------------------+
    | \x00\x02 (type: arp reply)               |
    +------------+-----------+-----------------+
    | Source MAC | Source IP | Destination MAC |
    +------------+---+-------+-----------------+
    | Destination IP | ... Frame Length: 42 ...
    +----------------+
    """
    ARPOP_REQUEST = pack('!H', 0x0001)
    ARPOP_REPLY = pack('!H', 0x0002)
    packet = b''

    sender_mac_b = pack('!6B', *[int(x, 16) for x in sender_mac.split(':')])
    zero_mac_b   = pack('!6B', *(0x00,) * 6)
    sender_ip_b  = pack('!4B', *[int(x) for x in sender_ip.split('.')])
    target_ip_b  = pack('!4B', *[int(x) for x in target_ip.split('.')])

    packet += pack('!6B', *(0xFF,) * 6)
    packet += sender_mac_b
    packet += b'\x08\x06'  # Type ARP
    packet += b'\x00\x01'  # Ethernet (HW TYPE)
    packet += b'\x08\x00'  # Protocol type IP
    packet += b'\x06'  # HW Size
    packet += b'\x04'  # Protocol size
    if arptype == 'REQUEST':
        packet += ARPOP_REQUEST
    else:
        packet += ARPOP_REPLY
    packet += sender_mac_b  # sender mac addr
    packet += sender_ip_b   # sender ip addr
    if arptype == 'REQUEST':
        packet += zero_mac_b  # Empty MAC
    else:
        packet += sender_mac_b
    packet += target_ip_b
    packet += b'\x00' * 18  # padding

    #defining the socket
    sock = socket.socket(socket.PF_PACKET, socket.SOCK_RAW)
    sock.bind((iface, 0x0806))

    # send the ARP
    sock.send(packet)
    while 1:
        srecv = select.select([sock], [], [], 0.5)
        # data
        if srecv[0]:
            try:
                data = sock.recv(42)  # ARP default packet size
            except:
                continue
            if data[12:14] == b'\x08\x06' and \
               data[20:22] == ARPOP_REPLY:  # check opcode is reply
                tgt_mac = prettify(data[6:12])
                logging.debug("%s is at %s" % (target_ip, tgt_mac))
                sock.close()
                return True
            else:
                break
        break

    # Did not receive any answer to our request, means IP is free
    return False


def find_free_ip(iface, ip, mac, netmask):
    '''
    Try to find a free ip on the subnet of iface
    '''
    exist = True
    test_ip = None
    while exist is True:
        test_ip = get_random_ip_in_subnet(ip, netmask)
        exist = send_arp(iface, ip, mac, test_ip, 'REQUEST')
    logging.debug("Using %s IP." % test_ip)
    return test_ip
