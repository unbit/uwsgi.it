Static only sites with uwsgi
----------------------------

Simple mode
-----------

```ini
[uwsgi]
plugin = 0:notfound

domain = mydomain.it

; set it to the path of not found page
error-page-404 = path_to_404.html

; the file to search when asking for directories
static-index = index.html

; the document root (you can specify it multiple times for fallbacks)
check-static = path_to_the_document_root

```

More infos here:

http://uwsgi-docs.readthedocs.org/en/latest/StaticFiles.html

Advanced mode
-------------

Having all of our static files in a common directory is the simplest
way to serve them. Unfortunately it may happen to have static files in
different directories.
The easiest configuration to handle this scenario is a *catch
all* rule:

```ini
[uwsgi]
plugin = router_static
domain = mydomain.it
basedir = $(HOME)/www/$(domain)
offload-threads = 2
route = ^/$ static:%(basedir)/index.html
route = /(.*) static:%(basedir)/$1
```

Please note that the specific rule for */* must be placed before the
*catch all* one.

Most of the time though we want to restrict the directories served.
To accomplish that better use a *regular expression group*:

```ini
[uwsgi]
plugin = router_static
domain = mydomain.it
basedir = $(HOME)/www/$(domain)
offload-threads = 2
route = ^/$ static:%(basedir)/index.html
route = /(img|css|js)/(.*) static:%(basedir)/$1/$2
```
