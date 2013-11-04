from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

from experiments.admin import marketadmin

urlpatterns = patterns(
    '',
    url(r'^$', TemplateView.as_view(template_name='index.html'), name='home'),
    url(r'^exp/', include('experiments.urls', 'exp', 'experiments')),
    url(r'^admin/', include(marketadmin.urls)),
)
