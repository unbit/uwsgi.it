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
