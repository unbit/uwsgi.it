from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

from uwsgi_it_api.decorators import need_basicauth, api_auth
from uwsgi_it_api.utils import spit_json, check_body, dns_check
from uwsgi_it_api.models import *
from uwsgi_it_api.config import UWSGI_IT_BASE_UID

import json
import datetime
import time
import uuid

@need_basicauth
@csrf_exempt
def portmappings(request, ip):
    customer = request.user.customer
    try:
        server = Server.objects.get(address=ip,owner=customer)
    except:
        return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
    if request.method == 'POST':
        response = check_body(request)
        if response:
            return response
        j = json.loads(request.read())
        if not j:
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        pm = Portmap()
        try:
            pm.proto = j['proto']
            pm.public_port = int(j['public_port'])
            pm.private_port = int(j['private_port'])
            pm.container = server.container_set.get(pk=(int(j['container']) - UWSGI_IT_BASE_UID), customer=customer)
            pm.full_clean()
            pm.save()
        except:
            import sys
            print sys.exc_info()
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        response = HttpResponse(json.dumps({'message': 'Created'}), content_type="application/json")
        response.status_code = 201
        return response
    elif request.method == 'DELETE':
        response = check_body(request)
        if response:
            return response
        j = json.loads(request.read())
        if not j:
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        try:
            pm = Portmap.objects.get(pk=j['id'], container__server=server)
            pm.delete()
        except:
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        return HttpResponse(json.dumps({'message': 'Ok'}), content_type="application/json")
    mappings = []
    for portmap in Portmap.objects.filter(container__server=server):
        mappings.append({'id': portmap.pk,
                         'proto': portmap.proto,
                         'public_port': portmap.public_port,
                         'container': portmap.container.uid,
                         'container_ip': str(portmap.container.ip),
                         'private_port': portmap.private_port,
                       })
    return spit_json(request, mappings)
    

@need_basicauth
@csrf_exempt
def container(request, id):
    customer = request.user.customer
    try:
        container = customer.container_set.get(pk=(int(id) - UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
    if request.method == 'POST':
        response = check_body(request)
        if response:
            return response
        allowed_keys = (
            'name', 'note', 'quota_threshold', 'jid', 'jid_secret',
            'jid_destinations', 'nofollow', 'pushover_user',
            'pushover_token', 'pushover_sound', 'alarm_freq',
            'pushbullet_token', 'slack_webhook',
            'custom_distros_storage',
        )

        j = json.loads(request.read())
        if not j:
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        for key in j:
            if key in allowed_keys:
                setattr(container, key, j[key])
        if 'ssh_keys' in j:
            container.ssh_keys_raw = '\n'.join(j['ssh_keys'])
            container.ssh_keys_mtime = datetime.datetime.now()
        if 'distro' in j:
            container.distro = Distro.objects.get(pk=j['distro'])
        if 'custom_distro' in j:
            container.custom_distro = CustomDistro.objects.filter(pk=j['custom_distro'], container__server=container.server, container__customer=customer).exclude(container=container)[0]
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
                    new_tags.append(Tag.objects.get(customer=customer, name=tag))
                except:
                    pass
            container.tags = new_tags
        # linking and unlinking requires reboot
        if 'link' in j:
            try:
                link = ContainerLink()
                link.container = container
                link.to = Container.objects.get(pk=(int(j['link']) - UWSGI_IT_BASE_UID))
                link.full_clean()
                link.save()
                container.last_reboot = datetime.datetime.now()
            except:
                response = HttpResponse(json.dumps({'error': 'Conflict'}), content_type="application/json")
                response.status_code = 409
                return response
        if 'unlink' in j:
            try:
                link = container.containerlink_set.get(to=(int(j['unlink']) - UWSGI_IT_BASE_UID))
                link.delete()
                container.last_reboot = datetime.datetime.now()
            except:
                response = HttpResponse(json.dumps({'error': 'Conflict'}), content_type="application/json")
                response.status_code = 409
                return response
        if 'reboot' in j:
            container.last_reboot = datetime.datetime.now()
        container.full_clean()
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
        'jid': container.jid,
        'jid_destinations': container.jid_destinations,
        'pushover_user': container.pushover_user,
        'pushover_token': container.pushover_token,
        'pushover_sound': container.pushover_sound,
        'pushbullet_token': container.pushbullet_token,
        'slack_webhook': container.slack_webhook,
        'alarm_freq': container.alarm_freq,
        'quota_threshold': container.quota_threshold,
        'nofollow': container.nofollow,
        'note': container.note,
        'linked_to': container.linked_to,
        'custom_distros_storage': container.custom_distros_storage,
        'custom_distro': None,
        'ssh_keys': container.ssh_keys,
        'tags': [t.name for t in container.tags.all()],
        'legion_address': [l.address for l in container.server.legion_set.all()]
    }
    if container.distro:
        c['distro'] = container.distro.pk
        c['distro_name'] = container.distro.name
    if container.custom_distro:
        c['custom_distro'] = container.custom_distro.pk
        c['custom_distro_name'] = container.custom_distro.name
    return spit_json(request, c)

def news(request):
    news_list = []
    user = api_auth(request)
    if user:
        for n in News.objects.all()[0:10]:
            news_list.append({'content': n.content,
                              'date': int(time.mktime(n.ctime.timetuple()))})
    else:
        for n in News.objects.filter(public=True)[0:10]:
            news_list.append({'content': n.content,
                              'date': int(time.mktime(n.ctime.timetuple()))})
    return spit_json(request, news_list)


@need_basicauth
@csrf_exempt
def me(request):
    customer = request.user.customer
    if request.method == 'POST':
        response = check_body(request)
        if response:
            return response
        allowed_keys = ('vat', 'company')
        j = json.loads(request.read())
        for key in j:
            if key in allowed_keys:
                setattr(customer, key, j[key])
        if 'password' in j:
            customer.user.set_password(j['password'])
            customer.user.save()
        if 'email' in j:
            customer.user.email = j['email']
            customer.user.save()
        customer.save()
    c = {
        'email': customer.user.email,
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
        if response:
            return response
        j = json.loads(request.read())
        needed_keys = ('server', 'name', 'memory', 'storage')
        for k in needed_keys:
            if not k in j.keys():
                return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        try:
            server = Server.objects.get(address=j['server'])
            if server.owner != request.user.customer:
                return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        except:
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        if int(j['memory']) > server.free_memory or int(j['memory']) <= 0:
            return HttpResponse(json.dumps({'error': 'Conflict', 'reason':'not enough memory'}), content_type="application/json")
        if int(j['storage']) > server.free_storage or int(j['storage']) <= 0:
            return HttpResponse(json.dumps({'error': 'Conflict', 'reason':'not enough storage'}), content_type="application/json")
        try:
            container = Container(customer=request.user.customer, server=server)
            container.name = j['name']
            container.memory = int(j['memory'])
            container.storage = int(j['storage'])
            container.save()
            response = HttpResponse(json.dumps({'message': 'Created'}), content_type="application/json")
            response.status_code = 201
            return response
        except:
            response = HttpResponse(json.dumps({'error': 'Conflict'}), content_type="application/json")
            response.status_code = 409
            return response
    elif (request.method == 'GET' and
         'tags' in request.GET):
            containers = request.user.customer.container_set.filter(tags__name__in=request.GET['tags'].split(','))
    else:
        containers = request.user.customer.container_set.all()

    c = []
    for container in containers:
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
            'custom_distro': None,
            'custom_distro_name': None,
            'server': container.server.name,
            'server_address': container.server.address,
            'tags': [t.name for t in container.tags.all()]
        }
        if container.distro:
            cc['distro'] = container.distro.pk
            cc['distro_name'] = container.distro.name
        if container.custom_distro:
            cc['custom_distro'] = container.custom_distro.pk
            cc['custom_distro_name'] = container.custom_distro.name
        c.append(cc)

    return spit_json(request, c)

@need_basicauth
@csrf_exempt
def loopboxes(request):
    if request.method == 'POST':
        response = check_body(request)
        if response:
            return response
        j = json.loads(request.read())
        needed_keys = ('container', 'filename', 'mountpoint')
        for k in needed_keys:
            if not k in j.keys():
                return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        try:
            container = request.user.customer.container_set.get(pk=(int(j['container']) - UWSGI_IT_BASE_UID))
        except:
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        try:
            loopbox = Loopbox(container=container)
            loopbox.filename = j['filename']
            loopbox.mountpoint = j['mountpoint']
            if 'ro' in j:
                loopbox.ro = j['ro']
            loopbox.save()
            response = HttpResponse(json.dumps({'message': 'Created'}), content_type="application/json")
            response.status_code = 201
            return response
        except:
            response = HttpResponse(json.dumps({'error': 'Conflict'}), content_type="application/json")
            response.status_code = 409
            return response
    elif request.method == 'GET':
        query = {}
        if 'tags' in request.GET:
            query['tags__name__in'] = request.GET['tags'].split(',')
        if 'container' in request.GET:
            try:
                query['container'] = request.user.customer.container_set.get(pk=(int(request.GET['container']) - UWSGI_IT_BASE_UID))
            except:
                return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        else:
            query['container__in'] = request.user.customer.container_set.all()
        loopboxes = Loopbox.objects.filter(**query)
    else:
        loopboxes = Loopbox.objects.filter(container__in=request.user.customer.container_set.all())

    l = []
    for loopbox in loopboxes:
        ll = {
            'id': loopbox.pk,
            'container': loopbox.container.uid,
            'filename': loopbox.filename,
            'mountpoint': loopbox.mountpoint,
            'ro': loopbox.ro,
            'tags': [t.name for t in loopbox.tags.all()]
        }
        l.append(ll)
    return spit_json(request, l)


@need_basicauth
@csrf_exempt
def alarms(request):
    query = {}
    if 'container' in request.GET:
        try:
            query['container'] = request.user.customer.container_set.get(pk=(int(request.GET['container']) - UWSGI_IT_BASE_UID))
        except:
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
    else:
        query['container__in'] = request.user.customer.container_set.all()

    if 'vassal' in request.GET:
        query['vassal'] = request.GET['vassal']

    if 'class' in request.GET:
        query['_class'] = request.GET['class']

    if 'color' in request.GET:
        query['color'] = request.GET['color']

    if 'level' in request.GET:
        query['level'] = int(request.GET['level'])

    if 'line' in request.GET:
        query['line'] = int(request.GET['line'])

    if 'filename' in request.GET:
        query['filename'] = request.GET['filename']

    if 'func' in request.GET:
        query['func'] = request.GET['func']

    alarms = Alarm.objects.filter(**query)

    a = []

    if 'with_total' in request.GET:
        response = {'total': alarms.count(), 'alarms': a}
    else:
        response = a

    if 'range' in request.GET:
        to = request.GET['range']
        try:
            if '-' in to:
                _from, to = to.split('-')
            else:
                _from = 0
            alarms = alarms[int(min(_from, to)):int(max(_from, to))]

        except:
            response = HttpResponse(json.dumps({'error': 'Requested Range Not Satisfiable'}), content_type="application/json")
            response.status_code = 416
            return response
        if _from > to:
            alarms = alarms.reverse()

    for alarm in alarms:
        aa = {
            'id': alarm.pk,
            'container': alarm.container.uid,
            'level': alarm.level,
            'color': alarm.color,
            'class': alarm._class,
            'vassal': alarm.vassal,
            'line': alarm.line,
            'filename': alarm.filename,
            'func': alarm.func,
            'unix': int(alarm.unix.strftime('%s')),
            'msg': alarm.msg
        }
        a.append(aa)

    return spit_json(request, response)


@need_basicauth
@csrf_exempt
def loopbox(request, id):
    customer = request.user.customer
    try:
        loopbox = Loopbox.objects.get(pk=id, container__in=customer.container_set.all())
    except:
        return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
    if request.method == 'POST':
        response = check_body(request)
        if response:
            return response
        j = json.loads(request.read())
        if not j:
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        if 'tags' in j:
            new_tags = []
            for tag in j['tags']:
                try:
                    new_tags.append(Tag.objects.get(customer=customer, name=tag))
                except:
                    pass
            loopbox.tags = new_tags
        loopbox.save()
    elif request.method == 'DELETE':
        loopbox.delete()
        return HttpResponse(json.dumps({'message': 'Ok'}), content_type="application/json")
    l = {
        'id': loopbox.pk,
        'container': loopbox.container.uid,
        'filename': loopbox.filename,
        'mountpoint': loopbox.mountpoint,
        'ro': loopbox.ro,
        'tags': [t.name for t in loopbox.tags.all()]
    }
    return spit_json(request, l)


@need_basicauth
@csrf_exempt
def alarm(request, id):
    customer = request.user.customer
    try:
        alarm = Alarm.objects.get(pk=id, container__in=customer.container_set.all())
    except:
        return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
    if request.method == 'DELETE':
        alarm.delete()
        return HttpResponse(json.dumps({'message': 'Ok'}), content_type="application/json")
    a = {
        'id': alarm.pk,
        'container': alarm.container.uid,
        'level': alarm.level,
        'color': alarm.color,
        'class': alarm._class,
        'line': alarm.line,
        'filename': alarm.filename,
        'func': alarm.func,
        'vassal': alarm.vassal,
        'unix': int(alarm.unix.strftime('%s')),
        'msg': alarm.msg
    }
    return spit_json(request, a)

@need_basicauth
@csrf_exempt
def custom_distro(request, id):
    customer = request.user.customer
    try:
        distro = CustomDistro.objects.get(pk=id, container__customer=customer)
    except:
        return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
    if request.method == 'DELETE':
        distro.delete()
        return HttpResponse(json.dumps({'message': 'Ok'}), content_type="application/json")
    if request.method == 'POST':
        response = check_body(request)
        if response:
            return response
        j = json.loads(request.read())
        allowd_fields = ('name', 'path', 'note')
        for field in allowed_fields:
            if field in j:
                setattr(distro, field, j[field])
        distro.full_clean()
        distro.save()
    d = {
        'id': distro.pk,
        'container': distro.container.uid,
        'name': distro.name,
        'path': distro.path,
        'note': distro.note,
        'uuid': distro.uuid,
    }
    return spit_json(request, d)
            

@need_basicauth
@csrf_exempt
def alarm_key(request, id):
    customer = request.user.customer
    try:
        container = customer.container_set.get(pk=(int(id) - UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
    container.alarm_key = str(uuid.uuid4())
    container.save()
    return HttpResponse(json.dumps({'message': 'Ok', 'alarm_key': container.alarm_key}), content_type="application/json")


def alarm_key_auth(request, id):
    if not 'key' in request.GET:
        return None
    key = request.GET['key']
    if len(key) != 36:
        return None
    try:
        container = Container.objects.get(pk=(int(id) - UWSGI_IT_BASE_UID), alarm_key=key)
        user = container.customer.user
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        return user
    except:
        pass
    return None

@need_basicauth(fallback=alarm_key_auth)
@csrf_exempt
def raise_alarm(request, id):
    customer = request.user.customer
    try:
        container = customer.container_set.get(pk=(int(id) - UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
    if request.method == 'POST':
        response = check_body(request)
        if response:
            return response
        alarm = Alarm(container=container, level=1)
        if 'color' in request.GET:
            color = request.GET['color']
            if not color.startswith('#'):
                color = '#' + color
            alarm.color = color
        alarm._class = request.GET.get('class', None)
        alarm.vassal = request.GET.get('vassal', None)
        alarm.line = request.GET.get('line', None)
        alarm.func = request.GET.get('func', None)
        alarm.filename = request.GET.get('filename', None)
        # user alarm by default
        alarm.level = 1
        if 'level' in request.GET:
            alarm.level = int(request.GET['level'])
            if alarm.level < 1:
                return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        if 'unix' in request.GET:
            alarm.unix = datetime.datetime.fromtimestamp(int(request.GET['unix']))
        else:
            alarm.unix = datetime.datetime.now()
        alarm.msg = request.read()
        try:
            alarm.save()
            response = HttpResponse(json.dumps({'message': 'Created'}), content_type="application/json")
            response.status_code = 201
            return response
        except:
            response = HttpResponse(json.dumps({'error': 'Conflict'}), content_type="application/json")
            response.status_code = 409
            return response
    response = HttpResponse(json.dumps({'error': 'Method not allowed'}), content_type="application/json")
    response.status_code = 405
    return response


@need_basicauth
def distros(request):
    j = [{'id': d.pk, 'name': d.name} for d in Distro.objects.all()]
    return spit_json(request, j)

@need_basicauth
@csrf_exempt
def custom_distros(request, id=None):
    customer = request.user.customer
    if not id:
        j = [{'id': d.pk, 'name': d.name, 'container': d.container.uid} for d in CustomDistro.objects.filter(container__customer=customer)]
        return spit_json(request, j)
    try:
        container = customer.container_set.get(pk=(int(id) - UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
    if request.method == 'POST':
        if not container.custom_distros_storage:
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        response = check_body(request)
        if response:
            return response
        j = json.loads(request.read())
        distro = CustomDistro(container=container) 
        allowed_fields = ('name', 'path', 'note')
        for field in allowed_fields:
            if field in j:
                setattr(distro, field, j[field])
        try:
            distro.full_clean()
            distro.save()
        except:
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")
        response = HttpResponse(json.dumps({'message': 'Created'}), content_type="application/json")
        response.status_code = 201
        return response
    j = [{'id': d.pk, 'name': d.name} for d in CustomDistro.objects.filter(container__server=container.server,container__customer=customer).exclude(container=container)]
    return spit_json(request, j)


@need_basicauth
@csrf_exempt
def domains(request):
    customer = request.user.customer

    if request.method == 'POST':
        response = check_body(request)
        if response:
            return response
        j = json.loads(request.read())
        if Domain.objects.filter(name=j['name']):
            response = HttpResponse(json.dumps({'error': 'Conflict'}), content_type="application/json")
            response.status_code = 409
            return response
        if dns_check(j['name'], customer.uuid):
            try:
                customer.domain_set.create(name=j['name'])
                response = HttpResponse(json.dumps({'message': 'Created'}), content_type="application/json")
                response.status_code = 201
            except:
                response = HttpResponse(json.dumps({'error': 'Conflict'}), content_type="application/json")
                response.status_code = 409
            return response
        else:
            return HttpResponseForbidden(json.dumps({'error': 'Forbidden'}), content_type="application/json")

    elif request.method == 'DELETE':
        response = check_body(request)
        if response:
            return response
        j = json.loads(request.read())
        try:
            customer.domain_set.get(name=j['name']).delete()
        except Domain.DoesNotExist:
            return HttpResponseNotFound(json.dumps({'error': 'Not found'}), content_type="application/json")
        return HttpResponse(json.dumps({'message': 'Ok'}), content_type="application/json")

    elif request.method == 'GET':
        if 'tags' in request.GET:
            j = [{'id': d.pk, 'name': d.name, 'uuid': d.uuid, 'tags': [t.name for t in d.tags.all()]} for d in
                 customer.domain_set.filter(tags__name__in=request.GET['tags'].split(','))]
        else:
            j = [{'id': d.pk, 'name': d.name, 'uuid': d.uuid, 'tags': [t.name for t in d.tags.all()]} for d in
                 customer.domain_set.all()]
        return spit_json(request, j)

    response = HttpResponse(json.dumps({'error': 'Method not allowed'}), content_type="application/json")
    response.status_code = 405
    return response


@need_basicauth
@csrf_exempt
def tags(request):
    customer = request.user.customer
    allowed_keys = ('name', 'note')
    if request.method == 'POST':
        response = check_body(request)
        if response:
            return response
        j = json.loads(request.read())
        tag = Tag(customer=customer)
        for key in allowed_keys:
            if key in j:
                setattr(tag, key, j[key])
        try:
            tag.save()
            j = {'id': tag.pk, 'name': tag.name, 'note': tag.note}
            response = spit_json(request, j)
            response.status_code = 201
            response.reason_phrase = 'Created'
        except:
            response = HttpResponse(json.dumps({'error': 'Conflict'}), content_type="application/json")
            response.status_code = 409
        return response

    elif request.method == 'GET':
        j = [{'id': t.pk, 'name': t.name} for t in Tag.objects.filter(customer=customer)]
        return spit_json(request, j)
    response = HttpResponse(json.dumps({'error': 'Method not allowed'}), content_type="application/json")
    response.status_code = 405
    return response


@need_basicauth
@csrf_exempt
def tag(request, id):
    customer = request.user.customer
    try:
        t = Tag.objects.get(customer=customer, pk=id)
    except:
        return HttpResponseNotFound(json.dumps({'error': 'Not found'}), content_type="application/json")

    allowed_keys = ('name', 'note')
    if request.method == 'POST':
        response = check_body(request)
        if response:
            return response
        j = json.loads(request.read())
        for key in allowed_keys:
            if key in j:
                setattr(t, key, j[key])
        try:
            t.save()
            j = {'id': t.pk, 'name': t.name, 'note': t.note}
            return spit_json(request, j)
        except:
            response = HttpResponse(json.dumps({'error': 'Conflict'}), content_type="application/json")
            response.status_code = 409
        return response
    elif request.method == 'GET':
        j = {'id': t.pk, 'name': t.name, 'note': t.note}
        return spit_json(request, j)
    elif request.method == 'DELETE':
        t.delete()
        return HttpResponse(json.dumps({'message': 'Ok'}), content_type="application/json")
    allowed_keys = ('name', 'note')
    response = HttpResponse(json.dumps({'error': 'Method not allowed'}), content_type="application/json")
    response.status_code = 405
    return response


@need_basicauth
@csrf_exempt
def domain(request, id):
    customer = request.user.customer
    try:
        domain = customer.domain_set.get(pk=id)
    except:
        return HttpResponseNotFound(json.dumps({'error': 'Not found'}), content_type="application/json")
    allowed_keys = ('note',)
    if request.method == 'POST':
        response = check_body(request)
        if response:
            return response
        j = json.loads(request.read())
        for key in allowed_keys:
            if key in j:
                setattr(domain, key, j[key])
        if 'tags' in j:
            new_tags = []
            for tag in j['tags']:
                try:
                    new_tags.append(Tag.objects.get(customer=customer, name=tag))
                except:
                    pass
            domain.tags = new_tags
        try:
            domain.save()
            j = {'id': domain.pk, 'name': domain.name, 'uuid': domain.uuid, 'tags': [t.name for t in domain.tags.all()],
                 'note': domain.note}
            return spit_json(request, j)
        except:
            response = HttpResponse(json.dumps({'error': 'Conflict'}), content_type="application/json")
            response.status_code = 409
        return response
    elif request.method == 'DELETE':
        domain.delete()
        return HttpResponse(json.dumps({'message': 'Ok'}), content_type="application/json")

    elif request.method == 'GET':
        j = {'id': domain.pk, 'name': domain.name, 'uuid': domain.uuid, 'tags': [t.name for t in domain.tags.all()],
             'note': domain.note}
        return spit_json(request, j)

    response = HttpResponse(json.dumps({'error': 'Method not allowed'}), content_type="application/json")
    response.status_code = 405
    return response
