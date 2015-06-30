Managing custom distributions
=============================

Starting from june 2015 you can use your personal distributions in addition
the the ones supplied by the platform (and shared by all customers).

Obviously, when you use your own distros, your uwsgi.it supplier could have difficulties
on support, so take in account that very probably if you choose to use a custom distro you will be on your own.

Another important topic is that your images must be constantly security checked (while platforms distros are checked by your uwsgi.it supplier). Do not forget to do it ! Using a custom distro could basically means you need to came back to doing lot of boring sysadmin tasks.

Not scared enough ? Let's start
===============================

Requirements and (Security) Limits
----------------------------------

You need a dedicated container (with very few memory, 64M should be more than enough) to store your distro images.

This container CANNOT use custom distros for itself, its only purpose is to serve images.

A custom_distro storage container can serve images only for containers running on its same server and for the same customer (your images cannot be shared with other customers)

A custom_distro storage container should not run vassals (albeit it is possible). This is a best practice to improve security.

Unless you give world write privileges to directories of your images, they are readonly. If you need to give write access to containers, give them world write privilege (this is not a big problem as images are not shared with other customers)

Setting up a custom_distros_storage container
---------------------------------------------

This is pretty easy, just set (via the api) the custom_distros_storage boolean field to true.

Your container will be restarted and a 'distros' directory will be created in the home.

Now you can create custom distros in this container.

The API
-------

Get the list of configured custom distros for your customer

```
GET /api/custom_distros/
```

Get the list of usable custom distros for a specific container (remember the requirements !)

```
GET /api/custom_distros/id
```

Create a new custom distro for the specified custom_distros_storage container (this container is different from the one before that is a generic container that can use the custom_distro)

```
POST /api/custom_distros/id

{
  "name": "new_distro",
  "path": "ubuntu0001",
  "note": "Hello World"
}
```

Get infos aboud a custom distro (id this time, is the id of the custom distro)

```
GET /api/custom_distro/id
```

Update a custom distro

```
POST /api/custom_distro/id

{
  "name": "new_name_for_the_distro"
}
```

Delete a custom distro

```
DELETE /api/custom_distro/id
```


Building distros
----------------

Now you can start building your distro images.

There are a bunch of ways to do it, but first you need to know about a couple of tunings you need
to do on images.

The following 2 directories must exist in the distro root (yes yes, they could be automatically created, but manually managing it ensure you do not use unchecked dirs as rootfs):

```
/.old_root
/containers
```

If your distro /etc/passwd does not contain an entry for your container uid, some commodity command could not work
as expected. You can add an entry in /etc/passwd or use this nss module (you should run the commands using the distro as the root fs, chroot is your friend):

```
git clone https://github.com/unbit/nss-unbit
cd nss-unbit
# requires running as root/sudo
make
```

then edit /etc/nsswitch.conf (in the distro root)

```
passwd:         compat unbit
group:          compat unbit
shadow:         compat unbit
...
```

If you want to use the uWSGI Emperor of your container you need a uwsgi installation.

The Emperor searches for the uwsgi binary in the following paths (and order, remember that /usr/local is automatically mapped to the home):

```
/containers/<container_uid>/bin/uwsgi
/usr/local/bin/uwsgi
/opt/unbit/uwsgi/uwsgi
```

You can eventually completely ignore the Emperor, and use a rc.local script to spawn your processes (place it into the etc dir in the home, the distro /etc/rc.local script will be ignored)

To create your distros you can use the venerable debootstrap:

```
debootstrap trusty your_dir
chroot your_dir
... run tuning commands ...
```

exit the chroot, make a tarball of the distro dir and upload it into the custom_distros_storage container

But with Docker (https://www.docker.com/) things could be way easier:

```
.. create your docker container and tune it ...
docker export image_id | gzip > image.tgz
```

and upload image.tgz in the custom_distros_storage container

Images tar must be exploded into the distros/<image_name> path (<image_name> is the value of the path field in the api)

Mapping custom distros to containers
------------------------------------

Each container as a 'custom_distro' field. Just set it ot the id of the distro you want to use. (Remember to get the list of allowed custom distros for that container)

Check list for when you have problems
-------------------------------------

If the /.old_root directory is not found, the container will fallback to the default distro set for the container. In such a case you will get an alarm too.

If the container does not start, reset custom_distro to null, wait for the container to restart back in the default distro and check logs/emperor.log for problems. Every operation on the distro image is reported there.

If your bash report "I have no name" as the prompt, it means your /etc/passwd does not contain and entry for your container uid, or you did not setup the unbit nss module.


Tips & Tricks
-------------


