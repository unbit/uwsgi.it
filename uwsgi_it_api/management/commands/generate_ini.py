from django.core.management.base import BaseCommand, CommandError
from django.template.loader import render_to_string
from uwsgi_it_api.models import Container
from uwsgi_it_api.config import UWSGI_IT_BASE_UID

class Command(BaseCommand):
    args = '<uid>'
    help = 'generate .ini file for the specified container uid'


    def handle(self, *args, **options):
        pk = args[0]
        container = Container.objects.get(pk=(int(pk)-UWSGI_IT_BASE_UID))
        self.stdout.write(render_to_string('vassal.ini', {'container': container}))
