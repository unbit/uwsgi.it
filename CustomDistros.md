Managing custom distributions
=============================

Starting from june 2015 you can use your personal distributions in addition
the the ones supplied by the platform (and shared by all customers).

Obviously when you use your own distros your uwsgi.it supplier could have difficulties
on support, so take in account that very probably if you choose to use a custom distro you are on your own.

Another important topic is that your images must be constantly security checked (while platforms distros are checked by your uwsgi.it supplier). Do not forget to do it ! Using a custom distro could basically means you need to came back to doing lot of boring sysadmin tasks.

Not scared enough ? Let's' start
--------------------------------

Requirements and (Security) Limits
----------------------------------

You need a dedicated container (with very few memory) to store your distro images.

This container CANNOT use custom distros for itself, its only purpose is to serve images.

A custom_distro storage container can serve images only for containers running on its same server and for the same customer (your images cannot be shared with other customers)

A custom_distro storage container should not run vassals (albeit it is possible). This is a best practice to improve security.

Unless you give world write privileges to directories of your images, they are readonly. If you need to give write access to containers, give them world write privilege (this is not a big problem as images are not shared with other customers)

The API
-------

```
/api/custom_distros/
```

```
/api/custom_distros/id
```

```
/api/custom_distro/id
```

Building distros
----------------

/.old_root

/containers

nss
/opt/unbit/uwsgi/uwsgi
vassals

Debootstrap

Docker

Check list for when you have problems
-------------------------------------

Tips & Tricks
-------------
