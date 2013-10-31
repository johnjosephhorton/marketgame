from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    'experiments.views',
    url('^$', 'index'),
)
