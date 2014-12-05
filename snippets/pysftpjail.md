Using pysftpserver/pysftpjail SFTP wrappers
===========================================

```sh
pip install pysftpserver
```

this will install pysftpjail in /usr/local/bin

Now edit the ssh key you want to "jail" forcing it to call "pysftpjail \<path\>"

```ssh
command="pysftpjail logs" ssh-rsa AAAA.......
```

this will "jail" the session to the logs directory.

The path is always relative to the home
