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

(the rvm_21 is the name of the plugin that will be generated, call it how you want/need but do use only letters, numbers and underscores)

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

to use another gemset:

```sh
rvm gemset create foobar
rvm gemset use foobar
gem install rack
```

and change vassal file to

```ini
[uwsgi]
plugin = 0:../rvm_21
gemset = ruby-2.1.0@foobar
rack = $(HOME)/myapp.ru
domain = uwsgi.org
```

Notes:

you only need to build a uwsgi plugin for every different ruby version, not gemset !!!

Running old rails 2.x on ruby 1.8.7
-----------------------------------

```sh
rvm install 1.8.7
```

```sh
/opt/unbit/uwsgi/uwsgi --build-plugin "/opt/unbit/uwsgi/src/plugins/rack rvm_187"
```

```
gem install rails -v 2.3.18
gem install rack
gem install thin
gem update --system 1.8.25
```

```ini
[uwsgi]
plugin = 0:../rvm_187
gemset = ruby-1.8.7-p374
rails = <path_to_rails_app_directory>
domain = uwsgi.org
```

the only difference is the usage of 'rails' option instead of 'rack'
