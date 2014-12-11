Using pysftpserver/pysftpjail SFTP wrappers
===========================================

pysftpserver is a python tool implementing the SFTP standard. You can write SFTP services simply subclassing
it. One of the included scripts (named pysftpjail) is a virtual chrooot/jail one.

Being a python module/tool you can install pysftpserver via "pip" (a python package manager)

```sh
pip install pysftpserver
```

this will install pysftpjail in /usr/local/bin (the path will be automatically created by pip)

Now edit the ssh keyyou want to "jail" (via the api or one of its gui) forcing it to call "pysftpjail \<path\>"

```ssh
command="pysftpjail logs" ssh-rsa AAAA.......
```

this will "jail" every session using this key to the logs directory.

Note: The path argument of pysftpjail is always relative to the home
