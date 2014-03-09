from django.shortcuts import render
from uwsgi_it_api.models import *
from uwsgi_it_api.config import UWSGI_IT_BASE_UID
from django.http import HttpResponse,HttpResponseForbidden,HttpResponseNotFound
from django.template.loader import render_to_string
import json
from functools import wraps
import base64
from django.contrib.auth import authenticate, login
import dns.resolver
from django.views.decorators.csrf import csrf_exempt

def check_body(request):
    if int(request.META['CONTENT_LENGTH']) > 65536:
        response = HttpResponse('Request entity too large\n')
        response.status_code = 413
        return response

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
        # first check for crossdomain
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response['Access-Control-Allow-Origin']  = '*'
            response['Access-Control-Allow-Methods']  = 'GET,POST,DELETE,OPTIONS'
            response['Access-Control-Allow-Headers']  = 'X-uwsgi-it-username,X-uwsgi-it-password'
            return response
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
        elif request.META.has_key('HTTP_X_UWSGI_IT_USERNAME') and request.META.has_key('HTTP_X_UWSGI_IT_PASSWORD'):
            uname = request.META['HTTP_X_UWSGI_IT_USERNAME']
            passwd = request.META['HTTP_X_UWSGI_IT_PASSWORD']
            user = authenticate(username=uname, password=passwd)
            if user and user.is_active:
                login(request, user)
                request.user = user
                response = func(request, *args, **kwargs)
                response['Access-Control-Allow-Origin']  = '*'
                return response
                
            
        response = HttpResponse('Unathorized\n')
        response.status_code = 401
        response['Access-Control-Allow-Origin']  = '*'
        response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
        return response
    return _decorator

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
        servers.append( str(resolver.query(ns, 'A')[0]) )
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
    

# Create your views here.
@need_certificate
def private_custom_services(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        j = [{'customer':service.customer.pk, 'config': service.config, 'mtime': service.munix, 'id': service.pk } for service in server.customservice_set.all()]
        return HttpResponse(json.dumps(j), content_type="application/json")
    except:
        return HttpResponseForbidden('Forbidden\n')

@need_certificate
def private_containers(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        j = [{'uid':container.uid, 'mtime': container.munix } for container in server.container_set.exclude(distro__isnull=True).exclude(ssh_keys_raw__exact='').exclude(ssh_keys_raw__isnull=True)]
        return HttpResponse(json.dumps(j), content_type="application/json")
    except:
        return HttpResponseForbidden('Forbidden\n')

@need_certificate
def private_container_ini(request, id):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        container = server.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
        if not container.distro or not container.ssh_keys_raw: raise Exception("invalid container")
        j = render_to_string('vassal.ini', {'container': container})
        return HttpResponse(j, content_type="text/plain")
    except:
        return HttpResponseForbidden('Forbidden\n')    

@need_certificate
def private_legion_nodes(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        nodes = [] 
        unix = server.munix
        for node in server.legion.server_set.all():
            if node.address != server.address:
                if node.munix > unix: unix = node.munix
                nodes.append(node.address)
        return HttpResponse(json.dumps({'unix': unix, 'nodes':nodes}), content_type="text/plain")
    except:
        return HttpResponseForbidden('Forbidden\n')    

@need_certificate
def private_nodes(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        nodes = []
        unix = server.munix
        for node in Server.objects.all():
            if node.address != server.address:
                if node.munix > unix: unix = node.munix
                nodes.append(node.address)
        return HttpResponse(json.dumps({'unix': unix, 'nodes':nodes}), content_type="text/plain")
    except:
        return HttpResponseForbidden('Forbidden\n')
    

@need_certificate
def private_domains_rsa(request):
    server = Server.objects.get(address=request.META['REMOTE_ADDR'])
    server_customers = Customer.objects.filter(container__server=server)
    j = []
    for customer in server_customers:
        domains = []
        for domain in customer.domain_set.all():
            domains.append({'name': domain.name, 'mtime': domain.munix})
        j.append({'rsa': customer.rsa_pubkey, 'domains': domains })
    return HttpResponse(json.dumps(j), content_type="application/json")

@need_basicauth
@csrf_exempt
def container(request, id):
    customer = request.user.customer
    try:
        container = customer.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden('Forbidden\n')
    if request.method == 'POST':
        response = check_body(request)
        if response: return response
        allowed_keys = ('name', 'note','quota_threshold', 'jid', 'jid_secret', 'jid_destinations')
        j = json.loads(request.read())
        if not j: return HttpResponseForbidden('Forbidden\n')
        for key in j:
            if key in allowed_keys:
                setattr(container, key, j[key])
        if 'ssh_keys' in j:
            container.ssh_keys_raw = '\n'.join(j['ssh_keys'])
        if 'distro' in j:
            container.distro = Distro.objects.get(pk=j['distro'])
        if 'tags' in j:
            new_tags = []
            for tag in j['tags']:
                try:
                    new_tags.append(Tag.objects.get(customer=customer,name=tag))
                except:
                    pass
            container.tags = new_tags
        if 'link' in j:
            try:
                link = ContainerLink()
                link.container = container
                link.to = Container.objects.get(pk=(int(j['link'])-UWSGI_IT_BASE_UID))
                link.full_clean()
                link.save()
            except:
                response = HttpResponse('Conflict\n')
                response.status_code = 409
                return response
        if 'unlink' in j:
            try:
                link = container.containerlink_set.get(to=(int(j['unlink'])-UWSGI_IT_BASE_UID))
                link.delete()
            except:
                response = HttpResponse('Conflict\n')
                response.status_code = 409
                return response
        container.save()
    c = {
        'uid': container.uid,
        'name': container.name,
        'hostname': container.hostname,
        'ip': str(container.ip),
        'memory': container.memory,
        'storage': container.storage,
        'uuid': container.uuid,
        'distro': None,
        'distro_name': None,
        'server': container.server.name,
        'server_address': container.server.address,
        'legion_address': None,
        'jid': container.jid,
        'jid_destinations': container.jid_destinations,
        'quota_threshold': container.quota_threshold,
        'note': container.note,
        'linked_to': container.linked_to,
        'ssh_keys': container.ssh_keys,
        'tags': [t.name for t in container.tags.all()]
    }
    if container.distro:
        c['distro'] = container.distro.pk
        c['distro_name'] = container.distro.name
    if container.server.legion:
        c['legion_address'] = container.server.legion.address
    return HttpResponse(json.dumps(c), content_type="application/json")

@need_basicauth
@csrf_exempt
def me(request):
    customer = request.user.customer
    if request.method == 'POST':
        response = check_body(request)
        if response: return response
        allowed_keys = ('vat', 'company')
        j = json.loads(request.read())
        for key in j:
            if key in allowed_keys:
                setattr(customer, key, j[key])
        if 'password' in j:
            customer.user.set_password(j['password'])
            customer.user.save()
        customer.save()
    c = {
        'vat': customer.vat,
        'company': customer.company,
        'uuid': customer.uuid,
        'containers': [cc.uid for cc in customer.container_set.all()],
    }
    return HttpResponse(json.dumps(c), content_type="application/json")

@need_basicauth
@csrf_exempt
def containers(request):
    c = []
    for container in request.user.customer.container_set.all():
        cc = {
            'uid': container.uid,
            'name': container.name,
            'hostname': container.hostname,
            'ip': str(container.ip),
            'memory': container.memory,
            'storage': container.storage,
            'uuid': container.uuid,
            'distro': None,
            'distro_name': None,
            'server': container.server.name,
            'server_address': container.server.address,
            'tags': [t.name for t in container.tags.all()]
        }
        if container.distro:
            cc['distro'] = container.distro.pk
            cc['distro_name'] = container.distro.name
        c.append(cc)
        

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
        response = check_body(request)
        if response: return response
        j = json.loads(request.read())
        if Domain.objects.filter(name=j['name']):
            response = HttpResponse('Conflict\n')
            response.status_code = 409
            return response
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

    elif request.method == 'DELETE':
        response = check_body(request)
        if response: return response
        j = json.loads(request.read())
        customer.domain_set.get(name=j['name']).delete()
        return HttpResponse('Ok\n')

    elif request.method == 'GET':
        if 'tags' in request.GET:
            j = [{'id':d.pk, 'name':d.name, 'uuid': d.uuid, 'tags': [t.name for t in d.tags.all()]} for d in customer.domain_set.filter(tags__name__in=request.GET['tags'].split(','))]
        else:
            j = [{'id':d.pk, 'name':d.name, 'uuid': d.uuid, 'tags': [t.name for t in d.tags.all()]} for d in customer.domain_set.all()]
        return HttpResponse(json.dumps(j), content_type="application/json")

    response = HttpResponse('Method not allowed\n')
    response.status_code = 405
    return response

@need_basicauth
@csrf_exempt
def tags(request):
    customer = request.user.customer
    allowed_keys = ('name', 'note')
    if request.method == 'POST':
        response = check_body(request)
        if response: return response
        j = json.loads(request.read())
        tag = Tag(customer=customer)
        for key in allowed_keys:
            if key in j:
                setattr(tag, key, j[key])
        try:
            tag.save()
            response = HttpResponse('Created\n')
            response.status_code = 201
        except:
            response = HttpResponse('Conflict\n')
            response.status_code = 409
        return response
        
    elif request.method == 'GET':
        j = [{'id':t.pk, 'name':t.name} for t in Tag.objects.filter(customer=customer)]
        return HttpResponse(json.dumps(j), content_type="application/json")
    response = HttpResponse('Method not allowed\n')
    response.status_code = 405
    return response

@need_basicauth
@csrf_exempt
def tag(request, id):
    customer = request.user.customer
    try:
        t = Tag.objects.get(customer=customer, pk=id)
    except:
        return HttpResponseNotFound('Not Found\n')        

    allowed_keys = ('name', 'note')
    if request.method == 'POST':
        response = check_body(request)
        if response: return response
        j = json.loads(request.read())
        for key in allowed_keys:
            if key in j:
                setattr(t, key, j[key])
        try:
            t.save()
            j = {'id':t.pk, 'name':t.name, 'note':t.note}
            return HttpResponse(json.dumps(j), content_type="application/json")       
        except:
            response = HttpResponse('Conflict\n')
            response.status_code = 409
        return response
    elif request.method == 'GET':
        j = {'id':t.pk, 'name':t.name, 'note':t.note}
        return HttpResponse(json.dumps(j), content_type="application/json")
    elif request.method == 'DELETE':
        t.delete()
        return HttpResponse('Ok\n')
    allowed_keys = ('name', 'note')
    response = HttpResponse('Method not allowed\n')
    response.status_code = 405
    return response

@need_basicauth
@csrf_exempt
def domain(request, id):
    customer = request.user.customer
    try:
        domain = customer.domain_set.get(pk=id)
    except:
        return HttpResponseNotFound('Not Found\n') 
    allowed_keys = ('note',)
    if request.method == 'POST':
        response = check_body(request)
        if response: return response
        j = json.loads(request.read())
        for key in allowed_keys:
            if key in j:
                setattr(domain, key, j[key])
        if 'tags' in j:
            new_tags = []
            for tag in j['tags']:
                try:
                    new_tags.append(Tag.objects.get(customer=customer,name=tag))
                except:
                    pass
            domain.tags = new_tags
        try:
            domain.save()
            j = {'id':domain.pk, 'name':domain.name, 'uuid': domain.uuid, 'tags': [t.name for t in domain.tags.all()], 'note':domain.note}
            return HttpResponse(json.dumps(j), content_type="application/json")
        except:
            response = HttpResponse('Conflict\n')
            response.status_code = 409
        return response
    elif request.method == 'DELETE':
        domain.delete()
        return HttpResponse('Ok\n')

    elif request.method == 'GET':
        j = {'id':domain.pk, 'name':domain.name, 'uuid': domain.uuid, 'tags': [t.name for t in domain.tags.all()], 'note':domain.note}
        return HttpResponse(json.dumps(j), content_type="application/json")

    response = HttpResponse('Method not allowed\n')
    response.status_code = 405
    return response

@need_basicauth
def container_metrics_cpu(request, id):
    container = request.user.customer.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
    j = [[m.unix, m.value] for m in container.cpucontainermetric_set.all()]
    return HttpResponse(json.dumps(j), content_type="application/json")

def metrics_container_do(request, id, func):
    server = Server.objects.get(address=request.META['REMOTE_ADDR'])
    container = server.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))

    if request.method == 'POST':
        response = check_body(request)
        if response: return response
        j = json.loads(request.read())
        func(container, j['unix'], j['value'])
        response = HttpResponse('Created\n')
        response.status_code = 201
    else:
        response = HttpResponse('Method not allowed\n')
        response.status_code = 405
    return response

@csrf_exempt
@need_certificate
def private_metrics_container_mem(request, id):
    def do(container, unix, value):
        container.memorycontainermetric_set.create(unix=unix,value=value)
    return metrics_container_do(request, id, do)

@csrf_exempt
@need_certificate
def private_metrics_container_cpu(request, id):
    def do(container, unix, value):
        container.cpucontainermetric_set.create(unix=unix,value=value)
    return metrics_container_do(request, id, do)

@csrf_exempt
@need_certificate
def private_metrics_container_io_read(request, id):
    def do(container, unix, value):
        container.ioreadcontainermetric_set.create(unix=unix,value=value)
    return metrics_container_do(request, id, do)

@csrf_exempt
@need_certificate
def private_metrics_container_io_write(request, id):
    def do(container, unix, value):
        container.iowritecontainermetric_set.create(unix=unix,value=value)
    return metrics_container_do(request, id, do)

@csrf_exempt
@need_certificate
def private_metrics_container_net_rx(request, id):
    def do(container, unix, value):
        container.networkrxcontainermetric_set.create(unix=unix,value=value)
    return metrics_container_do(request, id, do)

@csrf_exempt
@need_certificate
def private_metrics_container_net_tx(request, id):
    def do(container, unix, value):
        container.networktxcontainermetric_set.create(unix=unix,value=value)
    return metrics_container_do(request, id, do)

@csrf_exempt
@need_certificate
def private_metrics_container_quota(request, id):
    def do(container, unix, value):
        container.quotacontainermetric_set.create(unix=unix,value=value)
    return metrics_container_do(request, id, do)
