```
events {
        worker_connections 512;
}

daemon off;
 
http {
	include /etc/nginx/mime.types;
	client_body_temp_path /tmp 1 2;
	proxy_temp_path /tmp 1 2;
	fastcgi_temp_path /tmp 1 2;
	uwsgi_temp_path /tmp 1 2;
	scgi_temp_path /tmp 1 2;
	gzip  on;
	gzip_http_version 1.1;
	gzip_comp_level 2;
	gzip_types text/plain text/html text/css
                      application/x-javascript text/xml
                      application/xml application/xml+rss
                      text/javascript;

	server {
        	listen       8080;
                server_name  localhost;
                location / {
                    root   www;
                    index  index.html index.htm;
                }
        }
}

```
