from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.templatetags.admin_static import static
from django.template.response import TemplateResponse
from django import forms

from experiments.models import (Experiment,
                                Participant,
                                Session,
                                Event,
                                Item,
                                ChoiceSet,
                                Winner)
from experiments.forms import QuickExperiment

class MarketGameAdmin(AdminSite):
    def index(self, *args, **kwargs):
        kwargs.setdefault('extra_context',
                          {'title': 'Market Game'})
        return super(MarketGameAdmin, self).index(*args, **kwargs)

    def get_urls(self):
        urls = super(MarketGameAdmin, self).get_urls()
        my_urls = patterns(
            '',
            url('^quick-experiment/$', self.admin_view(self.quick_experiment_view), name='quick-experiment'),)
        return my_urls + urls

    def quick_experiment_view(self, request):
        if request.method == 'POST':
            form = QuickExperiment(request.POST)
            if form.is_valid():
                short_name = form.cleaned_data['short_name']
        else:
            form = QuickExperiment()

        media = forms.Media(js=[static('admin/js/%s' % url)
                                for url in ('core.js',
                                            'admin/RelatedObjectLookups.js',
                                            'jquery.min.js',
                                            'jquery.init.js')])
        context = {
            'title': 'Quick Experiment Creation',
            'form': form,
            'media': media  + form.media,
            'errors': form.errors
        }
        return TemplateResponse(request, 'admin/quick_experiment.html',
                                context, current_app=self.name)

marketadmin = MarketGameAdmin()


class ExperimentAdmin(admin.ModelAdmin):
    pass


class ParticipantAdmin(admin.ModelAdmin):
    pass


class SessionAdmin(admin.ModelAdmin):
    pass


class EventAdmin(admin.ModelAdmin):
    pass


class ItemAdmin(admin.ModelAdmin):
    pass


class ChoiceSetAdmin(admin.ModelAdmin):
    pass


class WinnerAdmin(admin.ModelAdmin):
    pass


marketadmin.register(Experiment, ExperimentAdmin)
marketadmin.register(Participant, ParticipantAdmin)
marketadmin.register(Session, SessionAdmin)
marketadmin.register(Event, EventAdmin)
marketadmin.register(Item, ItemAdmin)
marketadmin.register(ChoiceSet, ChoiceSetAdmin)
marketadmin.register(Winner, WinnerAdmin)
