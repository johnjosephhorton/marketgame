import redis
from rq import Connection, Queue
from django.core import urlresolvers
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.templatetags.admin_static import static
from django.contrib import messages
from django.contrib.auth.admin import User, UserAdmin, Group, GroupAdmin
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django import forms
from django.conf import settings

from experiments.models import (Experiment,
                                Participant,
                                Session,
                                Event,
                                Item,
                                ChoiceSet,
                                Winner)
from experiments.forms import QuickExperiment
from tasks import send_participants_emails


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
                experiment = Experiment.objects.create(
                    short_name=form.cleaned_data['short_name'],
                    show_bid_counts=form.cleaned_data['show_bid_counts'],
                    contact_name=form.cleaned_data['contact_name'],
                    contact_email=form.cleaned_data['contact_email'],
                    deadline=form.cleaned_data['deadline'])

                for name, email, quota in form.cleaned_data['participants']:
                    obj, created = Participant.objects.get_or_create(name=name,
                                                                     email=email)
                    session = Session.objects.create(
                        experiment=experiment,
                        participant=obj,
                        quota=quota)

                for name, amount in form.cleaned_data['items']:
                    obj, created = Item.objects.get_or_create(name=name,
                                                              amount=amount)
                    experiment.items.add(obj)

                experiment.save()

                if form.cleaned_data['start_on_create']:
                    redis_conn = redis.from_url(settings.REDIS_URL)
                    q = Queue(connection=redis_conn)
                    q.enqueue(send_participants_emails, experiment.short_name)
                    messages.add_message(request,
                                         messages.SUCCESS,
                                         'Starting experiment: sending out emails...')
                return redirect(urlresolvers.reverse('admin:experiments_experiment_change', args=(experiment.pk,)))
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


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session

    def clean(self):
        experiment = self.cleaned_data['experiment']
        session_quota = self.cleaned_data['quota']
        if session_quota >= experiment.items.count():
            raise forms.ValidationError('Session quota must be less than item count', code='invalid')

        return self.cleaned_data

class SessionInline(admin.TabularInline):
    model = Session
    form = SessionForm
    extra = 1
    fields = ('participant',
              'quota')

class ExperimentAdmin(admin.ModelAdmin):
    fields = ('short_name',
              'contact_name',
              'contact_email',
              'show_bid_counts',
              'deadline',
              'items')
    inlines = (SessionInline,)
    list_display = ('short_name',
                    'started',
                    'started_time',
                    'finished',
                    'finished_time',
                    'active',
                    'deadline')
    list_filter = ('started',
                   'finished',
                   'active')
    filter_horizontal = ('items',)
    actions = ['start_experiment', 'resend_emails']

    def start_experiment(self, request, queryset):
        if not queryset.filter(started=True).exists():
            self.message_user(request, 'Starting selected experiment(s)...')
        else:
            self.message_user(request, 'You have selected experiment(s) that have already started', messages.ERROR)
    start_experiment.short_description = 'Start selected experiments (will send emails to participants)'

    def resend_emails(self, request, queryset):
        if queryset.filter(started=True, active=True, finished=False).exists():
            self.message_user(request, 'Resending emails to participants...')
        else:
            self.message_user(request, 'Selected experiment(s) must be active, started and not finished', messages.ERROR)
    resend_emails.short_description = 'Resend emails to participants w/ incomplete sessions'


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


marketadmin.register(Group, GroupAdmin)
marketadmin.register(User, UserAdmin)
marketadmin.register(Experiment, ExperimentAdmin)
marketadmin.register(Participant, ParticipantAdmin)
marketadmin.register(Session, SessionAdmin)
marketadmin.register(Event, EventAdmin)
marketadmin.register(Item, ItemAdmin)
marketadmin.register(ChoiceSet, ChoiceSetAdmin)
marketadmin.register(Winner, WinnerAdmin)
