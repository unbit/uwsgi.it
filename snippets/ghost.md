Running the Ghost blog engine
=============================

Ghost (https://ghost.org/) is a blog engine written in nodejs.

The following steps will guide you in its installation in a uwsgi.it container.

Requirements: a domain name mapped to a container with at least 512M ram, a recent (post-2013) distribution.

Download the latest ghost zip file from https://ghost.org/download/ and explode in the 'ghost' directory in your home:

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
***************
