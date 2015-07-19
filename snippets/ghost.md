Running the Ghost blog engine
=============================

Ghost (https://ghost.org/) is a blog engine written in nodejs.

The following steps will guide you in its installation in a uwsgi.it container.

Requirements: a domain name mapped to a container with at least 512M ram, a recent (post-2013) distribution.

Download the latest ghost zip file from https://ghost.org/download/ and explode it in the 'ghost' directory in your home:

```sh
mkdir ghost
cd ghost
unzip <path_of_the_zip_file>
```

Prepare the environment to support both the 'node' and 'nodejs' binary name:

```sh
ln -s /usr/bin/nodejs /usr/local/bin/node
```

The install the required dependancies (from the ghost directory):

```sh
npm install --production
```

after a bunch of seconds, your setup will be complete and you can run your ghost instance:

```sh
npm start --production
```

when the instance is fully spawned (the first time will require a bit of time to create db structures) hit ctrl-c and go to your vassals directory.

The vassal file
---------------

Its objective is to spawn the ghost service and to forward requests from the domain to its port:

```ini
[uwsgi]
domain = your_domain_name
chdir = $(HOME)/ghost
plugin = router_http
route-run = http:127.0.0.1:2368
env = NODE_ENV=production
attach-daemon = node index.js
offload-threads = 1
logto = $(HOME)/logs/ghost.log
```

this configuration (call it ghost.ini) once dropped in the vassals directory will start the ghost server and will log any request to logs/ghost.log
