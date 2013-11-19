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
from django.utils.html import format_html

from experiments.models import (Experiment,
                                Participant,
                                Session,
                                Event,
                                Item,
                                ChoiceSet,
                                Winner)
from experiments.forms import QuickExperiment
from tasks import send_participants_emails, resend_participant_emails, pick_winners


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
                    q.enqueue(send_participants_emails, [experiment.pk])
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


class SessionInline(admin.TabularInline):
    model = Session
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
    actions = ['start_experiment', 'resend_emails', 'pick_winners']

    def start_experiment(self, request, queryset):
        if not queryset.filter(started=True).exists():
            redis_conn = redis.from_url(settings.REDIS_URL)
            q = Queue(connection=redis_conn)
            q.enqueue(send_participants_emails, list(queryset.values_list('pk', flat=True)))

            self.message_user(request, 'Starting selected experiment(s)...')
        else:
            self.message_user(request, 'You have selected experiment(s) that have already started', messages.ERROR)
    start_experiment.short_description = 'Start selected experiments (will send emails to participants)'

    def resend_emails(self, request, queryset):
        if queryset.filter(started=True, active=True, finished=False).exists():
            redis_conn = redis.from_url(settings.REDIS_URL)
            q = Queue(connection=redis_conn)
            q.enqueue(resend_participant_emails, list(queryset.values_list('pk', flat=True)))

            self.message_user(request, 'Resending emails to participants...')
        else:
            self.message_user(request, 'Selected experiment(s) must be active, started and not finished', messages.ERROR)
    resend_emails.short_description = 'Resend emails to participants w/ incomplete sessions'

    def pick_winners(self, request, queryset):
        if queryset.filter(started=True, finished=False).exists():
            redis_conn = redis.from_url(settings.REDIS_URL)
            q = Queue(connection=redis_conn)
            q.enqueue(pick_winners, list(queryset.values_list('pk', flat=True)))
            queryset.update(finished=True)
            self.message_user(request, 'Picking winners for selected experiment(s)...')
        else:
            self.message_user(request, 'The selected experiment(s) is finished or not started', messages.ERROR)
    pick_winners.short_description = 'Pick winners and finish experiment'


class ParticipantAdmin(admin.ModelAdmin):
    pass


class SessionAdmin(admin.ModelAdmin):
    list_display = ('participant',
                    'access_url',
                    'experiment',
                    'quota',
                    'has_emailed',
                    'has_completed')

    def access_url(self, obj):
        return format_html('<a href="{}" target="_blank">{}</a>',
                           '/exp/{}'.format(obj.access_token),
                           obj.access_token)
    access_url.short_description = 'Access Token'
    access_url.allow_tags = True


class EventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'participant', 'data', 'created')

    def participant(self, obj):
        return obj.session.participant

    def event_type_display(self, obj):
        return obj

class ItemAdmin(admin.ModelAdmin):
    pass


class ChoiceSetAdmin(admin.ModelAdmin):
    list_display = ('participant', 'bid_items', 'item_order')

    def participant(self, obj):
        return obj.session.participant

    def item_order(self, obj):
        return ', '.join(obj.order)

    def bid_items(self, obj):
        return ', '.join(obj.choices.filter(bid=True).values_list('item__name', flat=True))


class WinnerAdmin(admin.ModelAdmin):
    list_display = ('participant',
                    'item',
                    'experiment')


marketadmin.register(Group, GroupAdmin)
marketadmin.register(User, UserAdmin)
marketadmin.register(Experiment, ExperimentAdmin)
marketadmin.register(Participant, ParticipantAdmin)
marketadmin.register(Session, SessionAdmin)
marketadmin.register(Event, EventAdmin)
marketadmin.register(Item, ItemAdmin)
marketadmin.register(ChoiceSet, ChoiceSetAdmin)
marketadmin.register(Winner, WinnerAdmin)
