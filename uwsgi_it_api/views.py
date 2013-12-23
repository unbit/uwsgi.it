from django.shortcuts import render
from uwsgi_it_api.models import *
from uwsgi_it_api.config import UWSGI_IT_BASE_UID
from django.http import HttpResponse,HttpResponseForbidden
from django.template.loader import render_to_string
import json

# Create your views here.

def containers(request):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        j = [{'uid':container.uid, 'mtime': container.munix } for container in server.container_set.all()]
        return HttpResponse(json.dumps(j), content_type="application/json")
    except:
        import sys
        print sys.exc_info()
        return HttpResponseForbidden('Forbidden')

def container(request, id):
    try:
        server = Server.objects.get(address=request.META['REMOTE_ADDR'])
        container = server.container_set.get(pk=(int(id)-UWSGI_IT_BASE_UID))
        j = render_to_string('vassal.ini', {'container': container})
        return HttpResponse(j, content_type="text/plain")
    except:
        import sys
        print sys.exc_info()
        return HttpResponseForbidden('Forbidden')    
