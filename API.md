The uwsgi.it API
----------------

Public api (requires basic auth)
--------------------------------

GET /containers/<id>

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
