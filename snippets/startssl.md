#Creating free ssl certificates from startssl.com
================================================

> This little document aims to be a tutorial on how to use the class1 free ssl certificates you can grab from startssl.com

**On startssl.com**

1. Create an account and save your client certificate (used only to access startssl.com)
2. Follow startssl.com instructions and validate your domain.  If they ask you a mandatory subdomain, you can use www.

**From uwsgi ssh**

Choose or create a directory on your container and navigate to it, then create a .key and a .csr file, without providing any password/passphrase (important):

```
#create .key:
openssl genrsa -out foobar.key 2048

#create .csr:
openssl req -new -key foobar.key -out foobar.csr

#this last command will prompt for more informations. When asked for a 'common name', you MUST provide the domain name you are going to use, with or without 'www': that's irrilevant
```

**Back to startssl.com**

1. Use the wizard to generate the certificates. Skip the first step (you'll find a proper skip button)  
2. On the next screen, on the proper field, copy ALL the content (including header and footer) of the .csr file you generated
3. You will be given another code: copy and save it on a new file (say ssl.crt). This is not the final one.
4. You'll also be given 2 more .pem files. Merge them with the previous one:

```
cat ssl.crt sub.class1.server.ca.pem ca.pem > ca.crt

#this is the final, real certificate you will use on the server
#name is arbitrary
#On the final file, be sure that also line breaks are properly merged. For example:

-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----

and not

-----END CERTIFICATE----------BEGIN CERTIFICATE-----
```


**Back to uwsgi**

1. Upload the cs.crt file (or whatever name you used) to the container (ideally on the same folder of the other files above)
2. With the uwsgi tools or GUI, Create the domains and subdomains you need (then you'll probably have to wait for proper DNS propagation)
3. In $HOME/vassals/apache.ini pass the ca.key and ca.crt path, once for each domain needed:

```
#say that we placed our files in a new 'ssl' dir
ssl-domain = yourdomain.com $(HOME)/ssl/ca.key $(HOME)/ssl/ca.crt
ssl-domain = www.yourdomain.com $(HOME)/ssl/ca.key $(HOME)/ssl/ca.crt

#NOTE: the ssl-domain directives substitute the domain ones. So do not use both for the same domain. For example, dot not:

domain = yourdomain.com
ssl-domain = yourdomain.com $(HOME)/ssl/ca.key $(HOME)/ssl/ca.crt
```

Then restart the server:

```
#example with trusty distribution
APACHE_CONFDIR=$HOME/etc/apache2 apache2ctl -k restart
```

**DONE!**