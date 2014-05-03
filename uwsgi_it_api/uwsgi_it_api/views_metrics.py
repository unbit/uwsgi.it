from django.http import HttpResponseForbidden
from django.core.cache import get_cache

from uwsgi_it_api.config import UWSGI_IT_BASE_UID, UWSGI_IT_METRICS_CACHE
from uwsgi_it_api.decorators import need_basicauth
from uwsgi_it_api.utils import spit_json

import datetime

def metrics_container_do(request, container, qs, prefix):
    """
    you can ask metrics for a single day of the year (288 metrics is the worst/general case)
    if the day is today, the response is cached for 5 minutes, otherwise it is cached indefinitely
    """
    today = datetime.datetime.today()
    year = today.year
    month = today.month
    day = today.day
    if 'year' in request.GET:year = int(request.GET['year'])
    if 'month' in request.GET: month = int(request.GET['month'])
    if 'day' in request.GET: day = int(request.GET['day'])
    expires = 86400
    if day != today.day or month != today.month or year != today.year: expires = 300
    try:
        # this will trigger the db query
        if not UWSGI_IT_METRICS_CACHE: raise
        cache = get_cache(UWSGI_IT_METRICS_CACHE)
        j = cache.get("%s_%d_%d_%d_%d" % (prefix, container.uid, year, month, day))
        if not j:
            j = qs.get(year=year,month=month,day=day).json
            cache.set("%s_%d_%d_%d_%d" % (prefix, container.uid, year, month, day ), j, expires)
    except: 
        import sys
        print sys.exc_info()
        try:
            j = qs.get(year=year,month=month,day=day).json
        except:
            j = "[]"
    return spit_json(request, j, expires, True)

@need_basicauth
def metrics_container_cpu(request, id):
    customer = request.user.customer
    try:
        container = customer.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden('Forbidden\n')
    return metrics_container_do(request, container, container.cpucontainermetric_set, 'cpu')

@need_basicauth
def metrics_container_net_tx(request, id):
    customer = request.user.customer
    try:
        container = customer.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden('Forbidden\n')
    return metrics_container_do(request, container, container.networktxcontainermetric_set, 'net.tx')

@need_basicauth
def metrics_container_net_rx(request, id):
    customer = request.user.customer
    try:
        container = customer.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden('Forbidden\n')
    return metrics_container_do(request, container, container.networkrxcontainermetric_set, 'net.rx')

@need_basicauth
def metrics_container_io_read(request, id):
    customer = request.user.customer
    try:
        container = customer.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden('Forbidden\n')
    return metrics_container_do(request, container, container.ioreadcontainermetric_set, 'io.read')

@need_basicauth
def metrics_container_io_write(request, id):
    customer = request.user.customer
    try:
        container = customer.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden('Forbidden\n')
    return metrics_container_do(request, container, container.ioreadcontainermetric_set, 'io.write')

@need_basicauth
def metrics_container_mem(request, id):
    customer = request.user.customer
    try:
        container = customer.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden('Forbidden\n')
    return metrics_container_do(request, container, container.memorycontainermetric_set, 'mem')

@need_basicauth
def metrics_container_quota(request, id):
    customer = request.user.customer
    try:
        container = customer.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
    except:
        return HttpResponseForbidden('Forbidden\n')
    return metrics_container_do(request, container, container.quotacontainermetric_set, 'quota')

def metrics_domain_do(request, domain, qs, prefix):
    """
    you can ask metrics for a single day of the year (288 metrics is the worst/general case)
    if the day is today, the response is cached for 5 minutes, otherwise it is cached indefinitely
    """
    today = datetime.datetime.today()
    year = today.year
    month = today.month
    day = today.day
    if 'year' in request.GET:year = int(request.GET['year'])
    if 'month' in request.GET: month = int(request.GET['month'])
    if 'day' in request.GET: day = int(request.GET['day'])
    expires = 86400
    if day != today.day or month != today.month or year != today.year: expires = 300
    try:
        # this will trigger the db query
        if not UWSGI_IT_METRICS_CACHE: raise
        cache = get_cache(UWSGI_IT_METRICS_CACHE)
        j = cache.get("%s_%d_%d_%d_%d" % (prefix, domain.id, year, month, day))
        if not j:
            j_list = []
            for m in qs.filter(year=year,month=month,day=day):
                j_list.append('{ "container": %d, "metrics": %s }' % (m.container.uid, m.json))
            j = '[' + ','.join(j_list) + ']'
            cache.set("%s_%d_%d_%d_%d" % (prefix, domain.id, year, month, day ), j, expires)
    except:
        import sys
        print sys.exc_info()
        try:
            j_list = []
            for m in qs.filter(year=year,month=month,day=day):
                j_list.append('{ "container": %d, "metrics": %s }' % (m.container.uid, m.json))
            j = '[' + ','.join(j_list) + ']'
        except:
            j = "[]"
    return spit_json(request, j, expires, True)

@need_basicauth
def metrics_domain_net_rx(request, id):
    customer = request.user.customer
    try:
        domain = customer.domain_set.get(pk=id)
    except:
        return HttpResponseForbidden('Forbidden\n')
    return metrics_domain_do(request, domain, domain.networkrxdomainmetric_set, 'domain.net.rx')

@need_basicauth
def metrics_domain_net_tx(request, id):
    customer = request.user.customer
    try:
        domain = customer.domain_set.get(pk=id)
    except:
        return HttpResponseForbidden('Forbidden\n')
    return metrics_domain_do(request, domain, domain.networktxdomainmetric_set, 'domain.net.tx')

@need_basicauth
def metrics_domain_hits(request, id):
    customer = request.user.customer
    try:
        domain = customer.domain_set.get(pk=id)
    except:
        return HttpResponseForbidden('Forbidden\n')
    return metrics_domain_do(request, domain, domain.hitsdomainmetric_set, 'domain.hits')
