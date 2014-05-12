from django.http import HttpResponse
from django.utils.http import http_date
import dns.resolver
import json
import time


def spit_json(request, j, expires=0, raw=False):
    if raw:
        body = j
    else:
        body = json.dumps(j)
    if 'HTTP_USER_AGENT' in request.META:
        if 'curl/' in request.META['HTTP_USER_AGENT']:
            body += '\n'
    response = HttpResponse(body, content_type="application/json")
    if expires > 0:
        response['Expires'] = http_date(time.time() + expires)
    return response


def check_body(request):
    if int(request.META['CONTENT_LENGTH']) > 65536:
        response = HttpResponse(json.dumps({'error': 'Request entity too large'}), content_type="application/json")
        response.status_code = 413
        return response


def dns_check(name, uuid):
    resolver = dns.resolver.Resolver()
    resolver.timeout = 3
    # get nameservers list (max 4)
    try:
        ns_list = resolver.query(name, 'NS')
    except:
        ns_list = []
    if len(ns_list) > 4:
        ns_list = ns_list[0:4]
    servers = []
    for ns in ns_list:
        ns = str(ns)
        #print ns
        servers.append(str(resolver.query(ns, 'A')[0]))
    if servers:
        resolver.nameservers = servers

    parts = name.split('.')

    while len(parts) > 1:
        try:
            print '.'.join(parts)
            txt_list = resolver.query('.'.join(parts), 'TXT')
            for txt in txt_list:
                if 'uwsgi:%s' % uuid in str(txt):
                    return True
        except:
            pass
        parts = parts[1:]
    return False
