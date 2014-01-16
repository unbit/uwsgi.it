Using Perl local::lib for managing modules and packages
-------------------------------------------------------

For Saucy Salamander


```sh
perl -Mlocal::lib
```

then append to your .profile (create it if it does not exist):

```sh
[ $SHLVL -eq 1 ] && eval "$(perl -I$HOME/perl5/lib/perl5 -Mlocal::lib)"
```

logout and login back and install cpanminus:

```sh
curl -L http://cpanmin.us | perl - App::cpanminus
```

now you can install modules via cpanm:

(example)
```sh
cpanm Net::uwsgi
```

to use local::lib in your vassals files just add

```ini
[uwsgi]
...
perl-local-lib = $(HOME)/perl5
...
```
