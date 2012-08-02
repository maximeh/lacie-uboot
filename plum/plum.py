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


from math import floor
import logging
import os
import readline
# for history and elaborate line editing when using raw_input
# see http://docs.python.org/library/functions.html#raw_input
from select import select
import socket
from struct import pack
import sys
from time import sleep
sys.dont_write_bytecode = True

from network import iface_info, find_free_ip, is_valid_mac, is_valid_ipv4, ipcomm_info


class Plum(object):
    '''
    An instance of Plum is a session with the netconsole shell.
     '''

    def __init__(self):
        '''Sets some defaults'''

        self.ip_target = None
        self.bcast_addr = None
        self.mac_target = None
        self.send_port = 4446
        self.receive_port = 4445
        self.uboot_port = 6666
        self.lump_timeout = 120
        self.script = None
        self.do_wait = False
        self.progress = False
        self.debug = False

    def load_script(self, path_file):
        '''
        If we don't want an interactive shell, but a script to be executed.
        '''
        if not os.path.exists(path_file):
            logging.error("%s does not exists." % path_file)
        self.script = path_file

    def do_progress(self, new_progress):
        '''
        If set to true, we will print a progress bar instead of the output.
        '''
        self.progress = new_progress

    # Output example: [=======   ] 75%
    # width defines bar width
    # percent defines current percentage
    def print_progress(self, width, percent):
        marks = floor(width * (percent / 100.0))
        spaces = floor(width - marks)

        loader = '[' + ('=' * int(marks)) + (' ' * int(spaces)) + ']'

        sys.stdout.write("%s %d%%\r" % (loader, percent))
        if percent >= 100:
            sys.stdout.write("\n")
        sys.stdout.flush()

    def wait_at_reboot(self, wait):
        '''
        Set to true, we will wait for the device to reboot completely
        '''
        self.do_wait = wait

    def setup_network(self, net_dict):
        '''
        Give a dict with the following values to setup your network :
        {
            'iface': 'ethX'  # default : eth0
            'bcast_addr' : '255.255.255.0'  # The broadcast address if you need to set it
            'mac_target' : '00:00:00:00:00:00'  # The mac of your product
            'ip_target' : '192.168.1.1'  # The ip to assign to the product
        }
        '''

        if ('mac_target' not in net_dict) or (net_dict['mac_target'] is None):
            logging.info("WARNING : The first product to reboot will be catched !")
            logging.info("It may not be yours if multiple product reboot at the "
                         "same time on your network.")
            net_dict['mac_target'] = "00:00:00:00:00:00"

        try:
            ip, mac, netmask, bcast = iface_info(net_dict['iface'])
        except IOError:
            logging.error("Your network interface is not reachable."
                          " Is %s correct ?" % net_dict['iface'])
            return 1

        # This IP is used afterwards when TFTP'ing files
        if ('ip_target' not in net_dict) or (net_dict['ip_target'] is None):
            if sys.platform == "darwin":
                logging.error("You need to specify an IP to assign to the device.")
                return 1
            net_dict['ip_target'] = find_free_ip(net_dict['iface'], ip, netmask)

        # Check MAC and IP value.
        if not is_valid_mac(net_dict['mac_target']):
            logging.error("Your MAC address is not in the proper format."
                          "\'00:00:00:00:00:00\' format is awaited."
                          "You gave %s" % net_dict['mac_target'])
            return 1
        self.mac_target = net_dict['mac_target']

        if not is_valid_ipv4(bcast):
            logging.error("Your Broadcast IP is not in the proper format."
                          "\'W.X.Y.Z\' format is awaited."
                          "You gave %s" % bcast)
            return 1
        self.bcast_addr = bcast

        if not is_valid_ipv4(net_dict['ip_target']):
            logging.error("Your product IP is not in the proper format."
                          "\'W.X.Y.Z\' format is awaited."
                          "You gave %s" % net_dict['ip_target'])
            return 1
        self.ip_target = net_dict['ip_target']

    def send_lump(self):
        '''
        It will ask the users to reboot the target manually and then
        it will send LUMP packet to a target during 60s.
        '''

        # Create an array with 6 cases, each one is a member (int) of the MAC
        fields_macdest = [int(x, 16) for x in self.mac_target.split(':')]

        # Create an array with 4 cases, each one is a member (int) of the IP
        fields_ip = [int(x) for x in self.ip_target.split('.')]

        # Note : The empty MAC are 8 bytes in length according to the reverse
        # engineering done with WireShark. Don't know why exactly...
        pkt = pack('!I'   # LUMP
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
                          0x4C554D50,  # LUMP
                          0x44,
                          0x4D414344,  # MACD
                          0x10,
                          0x4D414340,  # MAC
                          0x8,
                          pack('!6B', *fields_macdest),  # int[] -> byte[]
                          0x49505300,  # IPS
                          0x0C,
                          0x49504000,  # IP
                          0x4,
                          pack('!4B', *fields_ip),  # int[] -> byte[]
                          0x4D414353,  # MACS
                          0x10,
                          0x4D414340,  # MAC
                          0x8)

        logging.debug("Sending some LUMP / Ctrl-C, "
                      "waiting for the NAS to start up")
        logging.info("Please /!\HARD/!\ reboot the device /!\NOW/!\ ")

        timeout = 0
        socket.setdefaulttimeout(60)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        try:
            sock.bind(('', self.uboot_port))
        except socket.error, err:
            logging.error("Couldn't be a udp server on port %d : %s",
                          self.uboot_port, err)
            sock.close()
            return None

        lump_ok = False
        while lump_ok is False and timeout < self.lump_timeout:
            sock.sendto(pkt, (self.bcast_addr, self.send_port))
            sleep(0.2)  # Wait for the device to process the LUMP
            #Send Ctrl-C (Code ASCII 3 for EXT equivalent of SIGINT for Unix)
            sock.sendto('\3', (self.bcast_addr, self.uboot_port))
            srecv = select([sock], [], [], 1)
            # data
            if not srecv[0]:
                continue
            try:
                serv_data = sock.recvfrom(1024)
                if serv_data[1][0] != self.ip_target:
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

        if timeout >= self.lump_timeout:
            logging.debug("Sending LUMP for %ds, no response !",
                           self.lump_timeout)
            lump_ok = False

        sock.close()
        return lump_ok

    def invoke(self, cmd, display=True):
        '''
        send a cmd
        '''

        # Empty command, nothing to do here
        if cmd == "":
            return 42

        exit_list = ['exit', 'reset']
        override = 'Override Env parameters? (y/n)'
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if cmd in exit_list:
            cmd = 'reset'
            cmd = pack('!' + str(len(cmd)) + 's1s', cmd, '\x0A')
            sock.sendto(cmd, (self.ip_target, self.uboot_port))
            sock.close()
            return 0

        sock.settimeout(10.0)
        try:
            sock.bind(('', self.uboot_port))
        except socket.error, err:
            logging.error("Can't open %d port. (Error : %s)",
                self.receive_port, err)
            sock.close()
            return 0

        #we want to send a cmd to the nas and get the reply in ans
        #every command is completed by \n !
        command = pack('!' + str(len(cmd)) + 's1s', cmd, '\x0A')
        sock.sendto(command, (self.ip_target, self.uboot_port))
        prompt = False
        len_command = 0

        while prompt is False:
            srecv = select([sock], [], [], 0.5)
            # data
            if not srecv[0]:
                continue
            try:
                data = sock.recvfrom(1024)
                if data[1][0] != self.ip_target:
                    continue
                recv_data = data[0]
                # check when prompt (Marvell>>) is available,
                if ("Marvell>> " == recv_data or override == recv_data):
                    if override == recv_data:
                        print recv_data
                    prompt = True
                # When sending a command U-Boot return the commands
                # char by char, we do this so we don't display it.
                elif len_command < len(command):
                    len_command += 1
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
                        cmd, self.receive_port, err)
        sock.close()
        return 42

    def run(self):
        '''
        Either we execute the script or we create an interactive shell
        to the netconsole.
        '''

        if not self.send_lump():
            logging.debug("LUMP was not sent/receveid by the target")
            return 1

        if self.script is not None:
            with open(self.script, 'r+') as script:
                script_cmd = script.readlines()

            if self.progress:
                # setup progress_bar
                p_width = 60
                p_pas = p_width / len(script_cmd)
                p_percent = 0

            for cmd in script_cmd:

                if self.progress:
                    # update the bar
                    self.print_progress(p_width, p_percent)
                    p_percent += p_pas

                if cmd == '\n' or cmd.startswith('#'):
                    continue

                if not self.progress:
                    print cmd.strip() + " => ",

                self.invoke(cmd.strip(), display=not self.progress)
                sleep(1)  # it seems uboot doesn't like being shaked a bit

            if self.progress:
                self.print_progress(p_width, 100)

            # You can't wait if there is no MAC.
            if self.do_wait and (self.mac_target != "00:00:00:00:00:00"):
                # Some command output may be stuck in the pipe
                sys.stdout.flush()
                # WAIT FOR THE DEVICE TO BOOT
                logging.info("Waiting for your product to reboot...")
                sleep(60 * 7)  # Wait 7mn, it should let the device to boot to find info.
                ip = ipcomm_info(self.receive_port, self.mac_target, self.ip_target)
                if ip is None:
                    logging.info("Timeout : Unable to get your product IP.")
                    return 1
                logging.info("Your product is available at %s" % ip)
            return 0

        exit_code = 42
        while(exit_code):
            exit_code = self.invoke(raw_input("Marvell>> "), display=True)
        return 0


def main():
    ''' launch everything '''

    import argparse
    from argparse import RawTextHelpFormatter

    parser = argparse.ArgumentParser(prog='plum', formatter_class=RawTextHelpFormatter)
    parser.add_argument('script', metavar='file', type=str, nargs='?',
                       help=argparse.SUPPRESS)
    parser.add_argument("-m", "--mac", dest="mac", action="store",
                      default=None,
                      help="Address MAC of the targeted device "
                      "(00:00:00:00:00:00)"
                      )
    parser.add_argument("-i", "--iface", dest="iface", action="store",
                      default="eth0",
                      help="Interface to use to send LUMP packet to.\n"
                      "Default is eth0.\n"
                      )
    parser.add_argument("--ip", dest="force_ip", action="store",
                      default=None,
                      help="Specify the IP address to assign to the device."
                      )
    parser.add_argument("-p", "--progress", dest="progress",
                      action="store_const", default=False, const=True,
                      help="Print a pretty progress bar,"
                      " use with a script shebang only.")
    parser.add_argument("-w", "--wait", dest="wait", action="store_const",
                      default=False, const=True,
                      help="Wait for the product to boot.\n"
                      "Note : Require the -m/--mac option to be set.\n")
    parser.add_argument("-D", "--debug", dest="loglevel", action="store_const",
                      const=logging.DEBUG, help="Output debugging information")

    session = Plum()

    if '-D' in sys.argv or '--debug' in sys.argv:
        session.debug = True
        logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(message)s')

    options = parser.parse_args()

    setup = {'mac_target': options.mac, 'iface': options.iface}
    if options.force_ip is not None:
        setup['ip_target'] = options.force_ip

    if session.setup_network(setup):
        return 1

    session.wait_at_reboot(options.wait)
    session.do_progress(options.progress)

    if options.script is not None and os.path.isfile(options.script):
        session.load_script(options.script)

    session.run()

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
