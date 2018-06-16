# TOO MANY OPEN FILES

### Find number of active connections in Linux using netstat

https://www.exchangecore.com/blog/find-number-active-connections-linux-using-netstat/

Finally, lets take a look at the big picture in a category form. It is often extremely useful to see what those connections are doing, especially when you think you might just have tons of open connections that are idle and are trying to tweak your settings. It's been known to happen where you have a really busy web server for instance, and maybe it's running a lot of database connections to the same box, then stopping. That often causes things like the TIME_WAIT to pile up and a large number for any of these may be an indication that you need to adjust your tcp timeout settings.

```bash
netstat -ant | awk '{print $6}' | sort | uniq -c | sort -n
      1 CLOSING
      1 established
      1 FIN_WAIT2
      1 Foreign
      2 CLOSE_WAIT
      6 FIN_WAIT1
      7 LAST_ACK
      7 SYN_RECV
     37 ESTABLISHED
     44 LISTEN
    297 TIME_WAIT
```

### What limits the maximum number of connections on a Linux server?

https://serverfault.com/questions/10852/what-limits-the-maximum-number-of-connections-on-a-linux-server

With this configuration I can run ab all day and never run out of connections:

```bash
net.ipv4.netfilter.ip_conntrack_max = 32768
net.ipv4.tcp_tw_recycle = 0
net.ipv4.tcp_tw_reuse = 0
net.ipv4.tcp_orphan_retries = 1
net.ipv4.tcp_fin_timeout = 25
net.ipv4.tcp_max_orphans = 8192
net.ipv4.ip_local_port_range = 32768    61000
```

### Increasing the maximum number of tcp/ip connections in linux

https://stackoverflow.com/questions/410616/increasing-the-maximum-number-of-tcp-ip-connections-in-linux

** On the Server Side: ** The `net.core.somaxconn` value has an important role. It limits the maximum number of requests queued to a listen socket. If you are sure of your server application's capability, bump it up from default 128 to something like 128 to 1024. Now you can take advantage of this increase by modifying the listen backlog variable in your application's listen call, to an equal or higher integer.

```sysctl net.core.somaxconn=1024```

### 遇到问题----linux-----linux 打开文件数 too many open files 解决方法

https://blog.csdn.net/zzq900503/article/details/54881848

```bash
ulimit -a

ulimit -n 32768
```

### command not found when using sudo ulimit [closed]

https://stackoverflow.com/questions/17483723/command-not-found-when-using-sudo-ulimit

ulimit is a shell builtin like cd, not a separate program. sudo looks for a binary to run, but there is no ulimit binary, which is why you get the error message. You need to run it in a shell.

However, while you do need to be root to raise the limit to 65535, you probably don’t want to run your program as root. So after you raise the limit you should switch back to the current user.

To do this, run:

```bash
sudo sh -c "ulimit -n 65535 && exec su $LOGNAME"
```
and you will get a new shell, without root privileges, but with the raised limit. The exec causes the new shell to replace the process with sudo privileges, so after you exit that shell, you won’t accidentally end up as root again.