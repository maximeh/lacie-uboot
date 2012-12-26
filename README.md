# lacie-uboot
### Access your LaCie NAS's U-Boot netconsole without any hardware.

## Available tools include:

  - lacie-uboot-shell : A simple U-Boot netconsole client.
  - lacie-nas-updater : A simple script using lacie-uboot-shell to update your
  system and/or bootloader.

The best way to use lacie-uboot-shell is to previously install it using :

```sh
$ sudo python setup.py install
# Then you will be able to execute lacie-uboot-shell from your path.
$ lacie-uboot-shell --help
```

Note: if you use the lacie-uboot tool suite outside of a standard
distribution installation, you may need to specify the Python module
search path with PYTHONPATH before executing the binaries:

```sh
$ export PYTHONPATH=./path/to/lacie-uboot
$ lacie-uboot-shell
Please /!\HARD/!\ reboot the device /!\NOW/!\
Marvell>>
```

## lacie-uboot-shell : U-Boot netconsole client

For help on how to use lacie-uboot-shell, type:

```sh
$ lacie-uboot-shell --help
```

If you have a fancy network system, you may specify the interface you want to
use with lacie-uboot-shell by setting the option -i followed by the network
interface name.

lacie-uboot-shell will try to look for a free IP on your subnet, if you want to
enforce the IP to set for your product, you should use the --ip option.

You may connect to your product using many different way, here are few examples
:

1.  You don't know the MAC of your product, then launch lacie-uboot-shell
    without the -m flag.

    ```sh
    $ lacie-uboot-shell
    ```

    Be careful, if you have multiple LaCie product on your network, the first to
    reboot will be catched ! It may not be yours...

2.  You know the MAC and don't want to bother finding a free ip :
    For example, to target 00:D0:4B:00:00:00 using the default iface (eth0):

    ```sh
    $ lacie-uboot-shell -m 00:D0:4B:00:00:00
    ```

3.  You know the MAC AND you want to enforce the IP :

    ```sh
    $ lacie-uboot-shell -m 00:D0:4B:00:00:00 --ip 192.168.13.37
    ```

When you are connected to your product through lacie-uboot-shell, type 'help' to
receive the list of available commands.

```sh
$ lacie-uboot-shell
Marvell>> help
...
```

## Scripting

If you happen to do a repetitive action with U-Boot, you can script that.
You only need to use lacie-uboot-shell as the shebang of your script :

```sh
#!/path/to/lacie-uboot-shell

setenv serverip 192.168.13.42
setenv ipaddr 192.168.13.37
[...]
bootm
```

Then you can call your script like that :

```sh
$ ./myscript -m 00:D0:4B:00:00:00 -i eth3 -p
```

You must also put an empty line at the end of your script
otherwise, the last line won't be executed.

If your script does not output anything, I recomend you to use the
-p option to print a pretty progress bar.

