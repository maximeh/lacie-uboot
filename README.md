plum - Python LaCie das U-Boot Milchkuh
=======================================

plum let you connect to the U-Boot netconsole of any
newgen LaCie product. It include a mini TFTP server.
It is written in Python and designed to be easy to use.

Available tools include:

  - plum : A simple U-Boot netconsole client.
  - capsup : A simple script using plum to update your system and/or bootloader.

plum support the --help option to present the usage summary to the
user.

The best way to use plum is to previously install it using :

    $ sudo python setup.py install
    # Then you will be able to execute plum from your path.
    $ plum --help

Note: if you use the plum tool suite outside of a standard
distribution installation, you may need to specify the Python module
search path with PYTHONPATH before executing the binaries:

    $ export PYTHONPATH=./path/to/plum
    $ plum
    Please /!\HARD/!\ reboot the device /!\NOW/!\
    Marvell>>


U-Boot netconsole client
------------------------

For help on how to use plum, type:

    $ plum --help

If you have a fancy network system, you may specify the interface you want plum
to use by setting the option -i followed by the network interface name.

plum will try to look for a free IP on your subnet, if you want to enforce the IP to set for your product, you should use the --ip option.

You may connect to your product using many differentway, here are few examples :

    1 - You don't know the MAC of your product
    Simply launch plum without -m argument.

    $ plum

    Using this way, if you have multiple LaCie product on your network, the first to reboot will be catched ! It may not be yours... be carefull !

    2 - You know the MAC and don't want to bother finding a free ip :
    For example, to target 00:D0:4B:00:00:00 using the default iface (eth0):

    $ plum -m 00:D0:4B:00:00:00

    3 - You know the MAC AND you want to enforce the IP used while using plum :

    $ plum -m 00:D0:4B:00:00:00 --ip 192.168.13.37


The plum client is an interactive client, just launch it and type 'help'
to see the available commands:

    $ plum
    Marvell>> help
    ...

Scripting
---------

You may want to script for a repeated action, for that you can create a script with plum as shebang, like this :

    #!/path/to/plum

    setenv serverip 192.168.13.42
    setenv ipaddr 192.168.13.37
    setenv bootargs ip=dhcp console=ttyS0,115200 netconsole=6666@${ipaddr}/,6666@${serverip}/ root=/dev/sda2 rootwait
    usb reset
    usbboot 0x800000 0:1
    usb stop
    bootm

Note the shebang , its mandatory if you want to make it work.
Then you can call your script like that (see previous section for other example on how to start plum) :

    $ ./myscript -m 00:D0:4B:00:00:00 -i eth3 -p

You must also put an empty line at the end of your script
otherwise, the last line won't be executed.

If your script does not output anything, I recomend you to use the
-p option to print a pretty progress bar.

Note
----

plum comes with opentfptd, it's a TFTP server written in C++ by Achal Dhir

