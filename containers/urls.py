from django.conf.urls import patterns

urlpatterns = patterns('containers.views',
    (r'^$', 'containers'),
    (r'^(\d+)$', 'container'),
)
