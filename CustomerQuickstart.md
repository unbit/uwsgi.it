Using uwsgi.it as a customer
----------------------------

When you buy/activate an account on a uwsgi.it-compliant service you will get:

an api base url: like https://foobar.com/api
an api username: like kratos
an api password: like deimos

With those parameters you will be able o configure your services using the HTTP api.

In this quickstart we will use the 'curl' command, but your supplier could give a you a more user-friendly interface (like a web-based one)
based on it.

Step 1: get your personal data
------------------------------

First step is ensuring your personal data are correct:

```sh
curl https://kratos:deimos@foobar.com/api/me/
```

```json
{
  "company": "God of war S.r.l.",
  "containers": [30001, 30004, 30007, 30008],
  "uuid": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
  "vat": "01234567890"
}
```
