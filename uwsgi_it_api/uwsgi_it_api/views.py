from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

from uwsgi_it_api.decorators import need_basicauth
from uwsgi_it_api.utils import spit_json, check_body, dns_check
from uwsgi_it_api.models import *
from uwsgi_it_api.config import UWSGI_IT_BASE_UID

import json

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
        allowed_keys = ('name', 'note','quota_threshold', 'jid', 'jid_secret', 'jid_destinations', 'nofollow')
        j = json.loads(request.read())
        if not j: return HttpResponseForbidden('Forbidden\n')
        for key in j:
            if key in allowed_keys:
                setattr(container, key, j[key])
        if 'ssh_keys' in j:
            container.ssh_keys_raw = '\n'.join(j['ssh_keys'])
        if 'distro' in j:
            container.distro = Distro.objects.get(pk=j['distro'])
        if 'memory' in j:
            if container.server.owner == customer:
                container.memory = int(j['memory'])
        if 'storage' in j:
            if container.server.owner == customer:
                container.storage = int(j['storage'])
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
        'nofollow': container.nofollow,
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
    return spit_json(request, c)

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
        'servers': [s.address for s in customer.server_set.all()],
    }
    return spit_json(request, c)

@need_basicauth
@csrf_exempt
def containers(request):
    if request.method == 'POST':
        response = check_body(request)
        if response: return response
        j = json.loads(request.read())
        needed_keys = ('server', 'name', 'memory', 'storage')
        for k in needed_keys:
            if not k in j.keys(): return HttpResponseForbidden('Forbidden\n')
        try:
            server = Server.objects.get(address=j['server'])
            if server.owner != request.user.customer:
                return HttpResponseForbidden('Forbidden\n') 
        except:
            return HttpResponseForbidden('Forbidden\n')
        try:
            container = Container(customer=request.user.customer,server=server)
            container.name = j['name']
            container.memory = int(j['memory'])
            container.storage = int(j['storage'])
            container.save()
            response = HttpResponse('Created\n')
            response.status_code = 201
            return response
        except:
            response = HttpResponse('Conflict\n')
            response.status_code = 409
            return response 
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
        

    return spit_json(request, c)

@need_basicauth
def distros(request):
    j = [{'id':d.pk, 'name':d.name} for d in Distro.objects.all()]
    return spit_json(request, j)

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
        return spit_json(request, j)

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
            j = {'id':tag.pk, 'name':tag.name, 'note':tag.note}
            response = spit_json(request, j)
            response.status_code = 201
            response.reason_phrase = 'Created'
        except:
            response = HttpResponse('Conflict\n')
            response.status_code = 409
        return response
        
    elif request.method == 'GET':
        j = [{'id':t.pk, 'name':t.name} for t in Tag.objects.filter(customer=customer)]
        return spit_json(request, j)
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
            return spit_json(request, j)
        except:
            response = HttpResponse('Conflict\n')
            response.status_code = 409
        return response
    elif request.method == 'GET':
        j = {'id':t.pk, 'name':t.name, 'note':t.note}
        return spit_json(request, j)
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
            return spit_json(request, j)
        except:
            response = HttpResponse('Conflict\n')
            response.status_code = 409
        return response
    elif request.method == 'DELETE':
        domain.delete()
        return HttpResponse('Ok\n')

    elif request.method == 'GET':
        j = {'id':domain.pk, 'name':domain.name, 'uuid': domain.uuid, 'tags': [t.name for t in domain.tags.all()], 'note':domain.note}
        return spit_json(request, j)

    response = HttpResponse('Method not allowed\n')
    response.status_code = 405
    return response
