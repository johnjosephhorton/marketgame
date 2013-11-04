from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    'experiments.views',
    url(r'^$', 'index'),
    url(r'^(?P<access_token>\w{32})/$', 'index', name='index-access-token')
)
