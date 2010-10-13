plum - Python LaCie das U-Boot Milchkuh
=======================================

plum let you connect to the U-Boot netconsole of any 
newgen LaCie product. It include a mini UDP server.
It is written in Python and designed to be fast,
and easy to use.

Available tools include:

  - plum : A simple U-Boot netconsole client.

plum support the --help option to present the usage summary to the
user.

Note: if you use the plum tool suite outside of a standard
distribution installation, you may need to specify the Python module
search path with PYTHONPATH before executing the binaries:

  $ export PYTHONPATH=./python-path
  $ bin/plum
  Please /!\HARD/!\ reboot the device /!\NOW/!\
  Marvell>>

U-Boot netconsole client
------------------------

For help on how to use plum, type:

  $ ./bin/plum --help

The IP can must be given using -i option. The MAC of the target is 
also mandatory and is given using the -m option.
For example, to target 192.168.0.6 with 00:D0:4B:00:00:00 :

  $ ./bin/plum -i 192.168.0.6 -m 00:D0:4B:00:00:00

The plum client is an interactive client, just launch it and type 'help'
to see the available commands:

  $ ./bin/plum
  Marvell>> help
  ...

You can create a script like this :

    #!/usr/bin/plum

    setup=(192.168.8.64 00:D0:4B:8B:35:3B)

    version
    help

Note the shebang and the setup= line, these two
things are mandatory if you want to make it work.

You must also put an emty line at the end of your script
otherwise, the last line won't be executed.

The order of the ip and mac in the setup does not matter.
If your script does not output anything, I recomend you to use the 
-p option with the shebang to print a pretty progress bar.
See the manual for this option.

