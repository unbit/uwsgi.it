from django.http import HttpResponse, HttpResponseForbidden
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from uwsgi_it_api.utils import spit_json, check_body
from uwsgi_it_api.decorators import need_certificate
from uwsgi_it_api.models import *
from uwsgi_it_api.config import UWSGI_IT_BASE_UID

import json
import datetime

@need_certificate
@csrf_exempt
def private_server_file_metadata(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        if request.method == 'POST':
            response = check_body(request)
            if response: return response
            j = json.loads(request.read())
            metadata = ServerFileMetadata.objects.get(filename=j['file'])
            sm, created = ServerMetadata.objects.get_or_create(server=server, metadata=metadata)
            sm.value = j['value']
            sm.save()
            response = HttpResponse('Created\n')
            response.status_code = 201
            return response
        files = []
        for _file in ServerFileMetadata.objects.all():
            files.append(_file.filename)
        return spit_json(request, files)
    except:
        import sys
        print sys.exc_info()
        return HttpResponseForbidden('Forbidden\n')

@need_certificate
def private_custom_services(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        j = [{'customer':service.customer.pk, 'config': service.config, 'mtime': service.munix, 'id': service.pk } for service in server.customservice_set.all()]
        return spit_json(request, j)
    except:
        return HttpResponseForbidden('Forbidden\n')

@need_certificate
def private_containers(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        j = [{'uid':container.uid, 'mtime': container.munix, 'ssh_keys_mtime': container.ssh_keys_munix } for container in server.container_set.exclude(distro__isnull=True).exclude(ssh_keys_raw__exact='').exclude(ssh_keys_raw__isnull=True)]
        return spit_json(request, j)
    except:
        return HttpResponseForbidden('Forbidden\n')

@need_certificate
def private_loopboxes(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        j = [{'id': loopbox.pk, 'uid':loopbox.container.uid, 'filename': loopbox.filename, 'mountpoint': loopbox.mountpoint, 'ro': loopbox.ro } for loopbox in Loopbox.objects.filter(container__server=server)]
        return spit_json(request, j)
    except:
        return HttpResponseForbidden('Forbidden\n')

@need_certificate
def private_portmappings(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        unix = server.portmappings_munix
        pmappings = []
        for portmap in Portmap.objects.filter(container__server=server):
            pmappings.append({
                             'proto': portmap.proto,
                             'public_ip': str(portmap.container.server.address),
                             'public_port': portmap.public_port,
                             'private_ip': str(portmap.container.ip),
                             'private_port': portmap.private_port,
                            })
            if portmap.munix > unix:
                unix = portmap.munix
        j = {'unix': unix, 'mappings':pmappings}
        return spit_json(request, j)
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
        import sys
        print sys.exc_info()
        return HttpResponseForbidden('Forbidden\n')    

@need_certificate
def private_container_ssh_keys(request, id):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        container = server.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
        if not container.distro or not container.ssh_keys_raw: raise Exception("invalid container")
        return HttpResponse(container.ssh_keys_raw, content_type="text/plain")
    except:
        return HttpResponseForbidden('Forbidden\n')

@need_certificate
def private_legion_nodes(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        nodes = [] 
        unix = server.munix
        if server.legion_set.count() > 0:
            for node in server.legion_set.first().nodes.all():
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
    return spit_json(request, j)

def private_metrics_domain_do(request, id, metric):
    server = Server.objects.get(address=request.META['REMOTE_ADDR'])
    container = server.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))

    if request.method == 'POST':
        response = check_body(request)
        if response: return response
        j = json.loads(request.read())
        d = datetime.datetime.fromtimestamp(int(j['unix']))
        domain = Domain.objects.get(name=j['domain'],customer=container.customer)
        try:
            m = metric.objects.get(domain=domain,container=container,year=d.year,month=d.month,day=d.day)
        except:
            m = metric(domain=domain,container=container,year=d.year,month=d.month,day=d.day,json='[]')
        m_json = json.loads(m.json)
        m_json.append( [int(j['unix']), long(j['value'])])
        m.json = json.dumps(m_json)
        m.save()
        response = HttpResponse('Created\n')
        response.status_code = 201
    else:
        response = HttpResponse('Method not allowed\n')
        response.status_code = 405
    return response

@csrf_exempt
@need_certificate
def private_metrics_domain_net_rx(request, id):
    return private_metrics_domain_do(request, id, NetworkRXDomainMetric)

@csrf_exempt
@need_certificate
def private_metrics_domain_net_tx(request, id):
    return private_metrics_domain_do(request, id, NetworkTXDomainMetric)

@csrf_exempt
@need_certificate
def private_metrics_domain_hits(request, id):
    return private_metrics_domain_do(request, id, HitsDomainMetric)

def private_metrics_container_do(request, id, metric):
    server = Server.objects.get(address=request.META['REMOTE_ADDR'])
    container = server.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))

    if request.method == 'POST':
        response = check_body(request)
        if response: return response
        j = json.loads(request.read())
        d = datetime.datetime.fromtimestamp(int(j['unix']))
        try:
            m = metric.objects.get(container=container,year=d.year,month=d.month,day=d.day)
        except:
            m = metric(container=container,year=d.year,month=d.month,day=d.day,json='[]')
        m_json = json.loads(m.json)
        m_json.append( [int(j['unix']), long(j['value'])])
        m.json = json.dumps(m_json)
        m.save()
        response = HttpResponse('Created\n')
        response.status_code = 201
    else:
        response = HttpResponse('Method not allowed\n')
        response.status_code = 405
    return response

@csrf_exempt
@need_certificate
def private_metrics_container_mem(request, id):
    return private_metrics_container_do(request, id, MemoryContainerMetric)

@csrf_exempt
@need_certificate
def private_metrics_container_mem_rss(request, id):
    return private_metrics_container_do(request, id, MemoryRSSContainerMetric)

@csrf_exempt
@need_certificate
def private_metrics_container_mem_cache(request, id):
    return private_metrics_container_do(request, id, MemoryCacheContainerMetric)

@csrf_exempt
@need_certificate
def private_metrics_container_cpu(request, id):
    return private_metrics_container_do(request, id, CPUContainerMetric)

@csrf_exempt
@need_certificate
def private_metrics_container_io_read(request, id):
    return private_metrics_container_do(request, id, IOReadContainerMetric)

@csrf_exempt
@need_certificate
def private_metrics_container_io_write(request, id):
    return private_metrics_container_do(request, id, IOWriteContainerMetric)

@csrf_exempt
@need_certificate
def private_metrics_container_net_rx(request, id):
    return private_metrics_container_do(request, id, NetworkRXContainerMetric)

@csrf_exempt
@need_certificate
def private_metrics_container_net_tx(request, id):
    return private_metrics_container_do(request, id, NetworkTXContainerMetric)

@csrf_exempt
@need_certificate
def private_metrics_container_quota(request, id):
    return private_metrics_container_do(request, id, QuotaContainerMetric)

@csrf_exempt
@need_certificate
def private_alarms(request, id):
    server = Server.objects.get(address=request.META['REMOTE_ADDR'])
    container = server.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
    if request.method != 'POST':
        response = HttpResponse('Method not allowed\n')
        response.status_code = 405
        return response
    response = check_body(request)
    if response: return response
    msg = request.read()
    if 'unix' in request.GET:
        d = datetime.datetime.fromtimestamp(int(request.GET['unix']))
    else:
        d = datetime.datetime.now()
    alarm = Alarm(container=container,unix=d)
    # system
    alarm.level = 0
    alarm.msg = msg
    alarm.save()
    response = HttpResponse('Created\n')
    response.status_code = 201
    return response
