The uwsgi.it API
----------------

Public api (requires basic auth)
--------------------------------

GET /me/
--------

returns the Customer's data:

```js
{
  "company": "Foobar S.r.l.", 
  "containers": [30005, 30003, 30002],
  "uuid": "xxxxxxxx-yyyy-zzzz-uuuu-aabbccddeeff",
  "vat": "11111111111"
}
```

containers is the list of containers id/uid

GET /me/containers/
-------------------

returns the list of containers

```js
{
  [
    {"uid": 30005, 
    "ip": "10.0.0.7",
    "name": "example",
    "uuid": "xxxxxxxx-yyyy-vvvv-ffff-cccccccccccc",
    "server_address": "1.2.3.4",
    "hostname": "example",
    "storage": 20000,
    "server": "server0002",
    "distro_name": "Saucy Salamander - Ubuntu 13.10 (64 bit)",
    "memory": 2000,
    "distro": 2
    }
  ]
}
```

get informations about a customer's container

POST /containers/<id>

update containers informations

GET /domains

returns the list of configured domains for the customer

POST /domains

add a new domain to the customer (involves a dns check for a specific TXT record)

GET /metrics/<id>/<arg>?from=X&to=Y

returns a list of metrics for the specified range


Private API (requires client certificate)
-----------------------------------------

GET /containers

returns the list of container for the asking server

GET /containers/<id>.ini

returns the .ini configuration for the specified container

POST /metrics/<id>/<arg>

insert a metric
