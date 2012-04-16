This server (opentftpdspV1.6x) is single port TFTP Server based on Trivial File
Transfer Protocol and is normally used for PXE Boot or firmware load. It
supports advance options like tsize, blksize, block number rollover and timeout.

There is one multiport version (opentftpdmtV1.6x) also available on website. If
you do not have firewall issues, you should use that. Multiport server accepts
all requests on listening port but responds on a new port for each request, using
a separate thread. Multithreaded version runs little faster.

On contrary, this single port server responds to requests back on same
listening port. This way firewall need to be opened for one port only.
Despite using single port, it too can serve multiple clients at same time.

If you are accessing TFTP Server using NAT Gateway, Multithreaded version of this
server will not be able to send the response back. This single port version will
work quite will through NAT Gateway too.

This is stable Release 1.66

CHANGES in 1.66

1) Bug about Listening in Daemon mode is fixed.

CHANGES in 1.64

1) The Server do not anymore listens on 0.0.0.0, it detects the interfaces dynamically
   and listens on each of them. This causes better performance.
2) Demonizing script is enchanced to use service and chkconfig commands.

CHANGES in 1.63

1) Logging has been changed, now new log file is created everyday and never overwritten.

CHANGES in 1.61

1) Program can be run as selected user, after starting as privileged user.
2) Can listen on 0.0.0.0 this would allow listening on all interfaces.
3) File buffering has been improved.

CHANGES  in 1.5

1) Bug about filename being too large is fixed
2) Read, Write and Overwrite permissions can be configured independently

BUGS FIXED in Release 1.41

1) LogFile bug fixed.

BUGS FIXED in Release 1.31
1) Max Block Size is 65503 now.
2) Code Cleanup and More Error Handling

NEW FEATURES in Release 1.3

1) Listening ports can also be specified. Ports more than 1024 do not need root account
2) Block size can now be as large as 65464.
3) Block Number rollover added, allowing transfer of files of any size.

NEW FEATURES in release 1.2

1) Multiple Listening Interfaces can be specified.
2) Logging has been added.
3) Multiple directories can be added to home using aliases
4) Permitted Hosts can be specified

DOWNLOAD

The latest version can be downloaded from http://tftp-server.sourceforge.net/

INSTALLATION

Expand the .gz file to an directory, using shell, goto that directory,
edit opentftpd.ini file (may just specify home dir), move opentftpd.ini
file to /etc directory or specify file locations with -i and -l flags.
For daemonizing, look at section DAEMONIZING below.

COMPILING

The included file opentftpd is an executive file for 32 bit Linux/Intel only.
YOU NEED TO RE-COMPILE ON Other Platforms like AIX, Solaris on GCC as:-

g++ opentftpd.cpp -oopentftpd -lpthread 
c++ opentftpd.cpp -oopentftpd -lsocket -lnsl -lpthread (on Solaris)

TESTING

This server runs in Debug Mode (with flag -v) or as Service (without any flag).
give following command as root:-

opentftpd#./opentftpd -v

You will see following results:-

Starting TFTP...
Alias / is mapped to /home/
Listening On: 192.168.0.19
Listening On: 127.0.0.1
Permitted Clients: All
max blksize: 9192
default blksize: 512
default interval: 5
Overwrite Existing Files: Yes

Accepting Requests...

Now open one more shell and give following commands:-

$tftp localhost
tftp>get [some file name in home dir]
Received 13112 bytes in 0.0 seconds

and on server you may see
client 127.0.0.1:xxxxx file ...... # blocks served

RUNNING

This program runs in two modes:-
a) Verbatim Mode (using -v argument)
b) Daemon (not using -v argument)

This program uses helper files:-
i)   -i[inifile], where configuration settings can be specified,
     default is /etc/opentftpd.ini
ii) -l[logfile] dumps log to this file in daemon mode, default is syslog

You can run as:-

/opt/opentftpdsp/opentftpd (daemon with default files)
/opt/opentftpdsp/opentftpd -v (verbatim with default files)
/opt/opentftpdsp/opentftpd -i inifile -l logfile (as daemon)
/opt/opentftpdsp/opentftpd -i inifile (as daemon)
/opt/opentftpdsp/opentftpd  -v -i inifile as verbatim

DAEMONIZING

If your system supports chkconfig command, you can use the enclosed
rc.opentftp file to add the service. Simply copy rc.opentftp as
/etc/init.d/opentftp (better just create a link to it as opentftp in init.d)
and make it executable. Also change the file paths (depending on where you
have installed the executive and log file directory) in this file.
Then you can use chkconfig command to add the daemon.

#ln -s /opt/opentftp/rc.opentftp /etc/init.d/opentftp
#chmod 755 /etc/init.d/opentftp
#chkconfig --add opentftp
#chkconfig opentftp on
Thats all you may need.

If you dont have chkconfig command, you can manually modify boot scripts
in /etc/rc.d/rc.local file or /etc/inittab file or /etc/rc.d/rc.inet2
file. Also you need to do following changes:-

Add the enclosed rc.opentftp script in /etc/rc.d and make it executable (755).
Also change the file paths (depending on where you have installed the executive
and log file directory) in this file. Finally you need to add the lines:-

# Start the Dual DHCP DNS Server daemon:
if [ -x /etc/rc.d/rc.opentftp ]; then
/etc/rc.d/rc.opentftp start
fi

to any of above scripts (preferably to /etc/rc.d/rc.inet2)

CONFIGURATION

You need home directory(s) to be set in opentftpd.ini file, and
move this ini file to /etc directory. you may leave other
parameters commented like blksize and interval.

You can use single directory as HOME directory. That case, all paths are 
appended to HOME directory. For example, your entry under [HOME] is:-

[HOME]
/opt/bootfiles

Then any request would be translated as
"get /myfile/bootfile.boot" to /opt/bootfiles/myfile/bootfile.boot on server.
it would be simply prepended to requested file path.

But if you use an alias like

[HOME]
a=/opt/bootfiles
b=/asdf/sdf/sfsd
c=/opt/sfrd/dsfr

Then your requests would be translated as:-

"get /a/myfile/bootfile.boot" to /opt/bootfiles/myfile/bootfile.boot
"get /b/myfile/bootfile.boot" to /asdf/sdf/sfsd/myfile/bootfile.boot
"get /c/myfile/bootfile.boot" to /opt/sfrd/dsfr/myfile/bootfile.boot

on server (alias would be substituted with it's value)

In this case any request, not starting with any of alias a,b,c would be errored out.
The advantage of using alias is you can specify multiple locations.

LICENSE

1) This program is released under GNU GENERAL PUBLIC LICENSE, Version 2, June 1991
2) This document is also released under above license.

DEBUG

If program is not responding:-

1) Ensure that you start this program as root only if listening on ports less than 1024.
   Even if you have specified username in ini file, program need to start as root for
   these ports and it will automatically switch to specified user, as it starts.
2) Run in verbatim mode first (with -v flag), it will provide all debug information
   as it verbatim the activities.
3) Errors like "bind failed" means another opentftpd is running and listening at same
   port (default 69). You can only have one server listening on a port at a time. It may also
   come if interface specified under [LISTEN-ON] is not physically available on Server.
   If you have specified [LISTEN-ON] option, check that ip and interface are Active.
   This error may still come if you are not starting the server as root, you cannot listen
   on ports less than 1024, refer point 1) above.
4) You may try recompiling (see COMPILING above).
5) Errors like "libstdc++.so.?: cannot open shared object file: No such file or directory" 
   are possible in some Unix/Linux flavors. Please recompile the program or create symbolic
   links:-
	ln -s /usr/local/lib/libstdc++.so.? /usr/lib/libstdc++.so.? 
	ln -s /usr/local/lib/libgcc_s.so.? /usr/lib/libgcc_s.so.?
   (? is library version as reported in error)
   or add the library path (directory where above file is) to env variable LD_LIBRARY_PATH.
6) Max size of file being transferred depends on block size, the max block count being 65536,
   it would be 512*65536 or 32MB. This limitation can be increased by increasing block size
   upto 65464 which makes the max file size to 4.2 GB. However the block size also depend on
   client. Most clients like Unix/Linux support block number rollover, which make the max 
   file size unlimited, irrespective of block size.

UNINSTALLATION

Just remove the program directory. You should also remove entries from initialize scripts of 
your machine.

BUGS

If you find any problem with this program or need more features, please send mail to achaldhir@gmail.com.
You may also send thanks email if it works fine for you.
	
DONATIONS

If you find that this program is suitable for your production environment and you are using it, Please
consider some donation for this project. Please dont be lazy about it. I have spent 100 hours on this
project but no donation has been received so far.