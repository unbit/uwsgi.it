from django.conf.urls import patterns

urlpatterns = patterns('uwsgi_it_api.views',
    (r'^containers/$', 'containers'),
    (r'^containers/(\d+)$', 'container'),
    (r'^containers/(\d+)\.ini$', 'container_ini'),
    (r'^me/$', 'me'),
    (r'^distros/$', 'distros'),
    (r'^domains/$', 'domains'),
    (r'^domains/rsa/$', 'domains_rsa'),
    (r'^domains/(\d+)$', 'domain'),
    (r'^metrics/container.io.read/(\d+)$', 'metrics_container_io_read'),
    (r'^metrics/container.io.write/(\d+)$', 'metrics_container_io_write'),
    (r'^metrics/container.net/(\d+)$', 'metrics_container_net'),
    (r'^metrics/container.cpu/(\d+)$', 'metrics_container_cpu'),
    (r'^metrics/container.mem/(\d+)$', 'metrics_container_mem'),
)
