from django.shortcuts import render
from uwsgi_it_api.models import *
from uwsgi_it_api.config import UWSGI_IT_BASE_UID
from django.http import HttpResponse,HttpResponseForbidden
from django.template.loader import render_to_string
import json
from functools import wraps
import base64
from django.contrib.auth import authenticate, login


def need_certificate(func):
    @wraps(func)
    def _decorator(request, *args, **kwargs):
        if request.META.has_key('HTTPS_DN'):
            return func(request, *args, **kwargs)
        else:
            return HttpResponseForbidden('Forbidden')
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
        response = HttpResponse('Unathorized')
        response.status_code = 401
        response['WWW-Authenticate'] = 'Basic realm="%s"' % realm
        return response
    return _decorator

# Create your views here.
@need_certificate
def containers(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        j = [{'uid':container.uid, 'mtime': container.munix } for container in server.container_set.all()]
        return HttpResponse(json.dumps(j), content_type="application/json")
    except:
        import sys
        print sys.exc_info()
        return HttpResponseForbidden('Forbidden')

@need_certificate
def container_ini(request, id):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        container = server.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
        j = render_to_string('vassal.ini', {'container': container})
        return HttpResponse(j, content_type="text/plain")
    except:
        import sys
        print sys.exc_info()
        return HttpResponseForbidden('Forbidden')    

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
