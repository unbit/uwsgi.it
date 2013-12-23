from django.shortcuts import render
from uwsgi_it_api.models import *
from uwsgi_it_api.config import UWSGI_IT_BASE_UID
from django.http import HttpResponse,HttpResponseForbidden
from django.template.loader import render_to_string
import json
from functools import wraps
import base64
from django.contrib.auth import authenticate, login
import dns.resolver
from django.views.decorators.csrf import csrf_exempt


def need_certificate(func):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        if request.META.has_key('HTTPS_DN'):
            return func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('Forbidden\n')
    return _decorator

def need_basicauth(func, realm='uwsgi.it api'):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        if request.META.has_key('HTTP_AUTHORIZATION'):
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2:
                if auth[0].lower() == "basic":
                    uname, passwd = base64.b64decode(auth[1]).split(':')
                    user = authenticate(username=uname, password=passwd)
                    if user and user.is_active:
                        login(request, user)
                        request.user = user
                        return func(request, *args, **kwargs)
        response = HttpResponse('Unathorized\n')
        response.status_code = 401
        response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
        return response
    return _decorator

def dns_check(name, uuid):
    resolver = dns.resolver.Resolver()
    resolver.timeout = 3
    # get nameservers list (max 4)
    ns_list = resolver.query(name, 'NS')
    if len(ns_list) > 4:
        ns_list = ns_list[0:4]
    servers = []
    for ns in ns_list:
        ns = str(ns)
        #print ns
        servers.append( str(resolver.query(ns, 'A')[0]) )
    if servers:
        resolver.nameservers = servers

    txt_list = resolver.query(name, 'TXT') 

    for txt in txt_list:
        if 'uwsgi:%s' % uuid in str(txt):
            return True
    return False
    

# Create your views here.
@need_certificate
def containers(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        j = [{'uid':container.uid, 'mtime': container.munix } for container in server.container_set.all()]
        return HttpResponse(json.dumps(j), content_type="application/json")
    except:
        return HttpResponseForbidden('Forbidden\n')

@need_certificate
def container_ini(request, id):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        container = server.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
        j = render_to_string('vassal.ini', {'container': container})
        return HttpResponse(j, content_type="text/plain")
    except:
        return HttpResponseForbidden('Forbidden\n')    

@need_basicauth
def container(request, id):
    container = request.user.customer.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
    c = {
        'uid': container.uid,
        'name': container.name,
        'hostname': container.hostname,
        'ip': str(container.ip),
        'memory': container.memory,
        'storage': container.storage,
        'uuid': container.uuid,
        'distro': container.distro.pk,
        'distro_name': container.distro.name,
        'server': container.server.name,
        'note': container.note,
        'ssh_keys': container.ssh_keys_raw,
    }
    return HttpResponse(json.dumps(c), content_type="application/json")

@need_basicauth
def me(request):
    customer = request.user.customer
    c = {
        'vat': customer.vat,
        'company': customer.company,
        'uuid': customer.uuid,
        'containers': [cc.uid for cc in customer.container_set.all()],
    }
    return HttpResponse(json.dumps(c), content_type="application/json")

@need_basicauth
def distros(request):
    j = [{'id':d.pk, 'name':d.name} for d in Distro.objects.all()]
    return HttpResponse(json.dumps(j), content_type="application/json")

@need_basicauth
@csrf_exempt
def domains(request):
    customer = request.user.customer
    if request.method == 'POST':
        if int(request.META['CONTENT_LENGTH']) > 65536:
            response = HttpResponse('Request entity too large\n')
            response.status_code = 413
            return response
        j = json.loads(request.read())
        if dns_check(j['name'], customer.uuid):
            try:
                customer.domain_set.create(name=j['name'])
                response = HttpResponse('Created\n')
                response.status_code = 201
            except:
                response = HttpResponse('Conflict\n')
                response.status_code = 409
            return response
        else:
            return HttpResponseForbidden('Forbidden\n')
    j = [{'id':d.pk, 'name':d.name, 'uuid': d.uuid} for d in customer.domain_set.all()]
    return HttpResponse(json.dumps(j), content_type="application/json")
