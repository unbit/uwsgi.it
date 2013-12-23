from django.conf.urls import patterns

urlpatterns = patterns('uwsgi_it_api.views',
    (r'^containers/$', 'containers'),
    (r'^containers/(\d+)$', 'container'),
    (r'^containers/(\d+)\.ini$', 'container_ini'),
)
