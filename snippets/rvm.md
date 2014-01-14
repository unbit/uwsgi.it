Using RVM
---------

For Saucy Salamander

```sh
curl -sSL https://get.rvm.io | bash -s stable
source .rvm/scripts/rvm
```

now you can install the ruby version you need

```sh
rvm install 2.1
```

and build the related uwsgi plugin:

```sh
/opt/unbit/uwsgi/uwsgi --build-plugin "/opt/unbit/uwsgi/src/plugins/rack rvm_21"
```

install the rack gem

```sh
gem install rack
```

and modify your uWSGI vassal file to load the new plugin and the new gemset:

```ini
[uwsgi]
plugin = 0:../rvm_21
gemset = ruby-2.1.0
rack = $(HOME)/myapp.ru
domain = uwsgi.org
```
