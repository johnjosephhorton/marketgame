import pusher
import json
import redis
from rq import Connection, Queue
from django.shortcuts import render, redirect, get_object_or_404
from django.template.response import TemplateResponse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.utils.timezone import now
from django.conf import settings
from django.contrib import messages
from django import forms

from experiments.models import (Experiment,
                                Event,
                                ChoiceSet,
                                Choice,
                                Item,
                                Session)
from experiments.forms import BiddingForm
from tasks import pick_winners


def get_bidding_form(experiment):
    form = BiddingForm()

    items = experiment.items.all()
    for item in items:
        data_attrs = {
            'data-amount': str(item.amount),
        }

        if experiment.show_bid_counts:
            # certainly inefficient
            saved_bids = experiment.sessions.filter(
                choice_set__choices__item=item,
                choice_set__choices__bid=True).count()
            data_attrs['data-saved-bids'] = saved_bids

        form.fields[item.name] = forms.BooleanField(required=False,
                                                    widget=forms.CheckboxInput(attrs=data_attrs))
    return form


def index(request, access_token=None):
    if access_token is None:
        return redirect('home')

    r = redis.from_url(settings.REDIS_URL)
    q = Queue(connection=r)
    session = get_object_or_404(Session, access_token=access_token)
    experiment = session.experiment

    # deadline check
    if now() >= experiment.deadline and not experiment.finished:
        experiment.finished = True
        experiment.finished_time = now()
        experiment.save()
        q.enqueue(pick_winners, [experiment.pk])
        messages.add_message(request,
                             messages.ERROR,
                             'Your session has already expired.', extra_tags='alert-danger')
        return redirect('home')

    if session.has_completed:
        messages.add_message(request,
                             messages.ERROR,
                             'You have already completed bidding.', extra_tags='alert-danger')
        return redirect('home')

    if not experiment.is_active():
        messages.add_message(request,
                             messages.ERROR,
                             'Bidding is closed.', extra_tags='alert-danger')
        return redirect('home')

    form = get_bidding_form(experiment)

    context = {
        'session': session,
        'experiment': experiment,
        'pusher_api_key': settings.PUSHER_KEY,
        'access_token': access_token,
        'form': form,
    }

    if request.method == 'POST':
        # process submitted bids
        form.data = request.POST
        form.is_bound = True
        if form.is_valid():
            choice_set, created = ChoiceSet.objects.get_or_create(
                session=session,
                order=[w.strip() for w in form.cleaned_data['ordering'].split(',')])
            available_items = experiment.items
            for field in form.visible_fields():
                bid = form.cleaned_data[field.name]
                choice_set.choices.create(item=available_items.get(name=field.name), bid=bid)
                # decrement unsaved bid because bid has been saved
                if bid:
                    r.hincrby(experiment.short_name, field.name, -1)
            session.has_completed = True
            session.save()

            session.events.create(event_type='exp_finished')
            # check if all sessions completed
            if not experiment.sessions.filter(has_completed=False).exists():
                experiment.finished = True
                experiment.finished_time = now()
                experiment.save()
                q.enqueue(pick_winners, [experiment.pk])

            return render(request, 'experiments/complete.html', context)
        else:
            messages.add_message(request,
                                 messages.ERROR,
                                 'Form submission error.', extra_tags='alert-danger')
            return render(request, 'experiments/index.html', context)
    else:
        form.fields['quota'].initial = session.quota
        return render(request, 'experiments/index.html', context)


def event(request, access_token):
    if not request.is_ajax():
        return HttpResponseBadRequest()
    if not request.method == 'POST':
        return HttpResponseBadRequest()

    def get_unsaved_bids(experiement, key):
        # return current unsaved bids
        unsaved_bids = r.hgetall(key)
        # experiment doesn't exist
        if not unsaved_bids:
            unsaved_bids = {item: '0' for
                     item in experiment.items.values_list('name', flat=True)}
            r.hmset(key, unsaved_bids)
            r.expire(key, 3600)
        return unsaved_bids

    session = get_object_or_404(Session, access_token=access_token)
    experiment = session.experiment
    exp_key = experiment.short_name

    if not experiment.is_active() or session.has_completed:
        return HttpResponseNotAllowed()

    p = pusher.pusher_from_url(url=settings.PUSHER_URL)
    r = redis.from_url(settings.REDIS_URL)

    data = json.loads(request.POST['data'])
    event = data['event']
    if event == 'new-participant':
        session.events.create(event_type='exp_started', data=data)
        return HttpResponse(json.dumps({'result': get_unsaved_bids(experiment, exp_key)}),
                            content_type='application/javascript')
    elif event == 'item-bid':
        # update item bid, then trigger event
        item = data['item']
        bid = data['bid']
        if r.exists(exp_key):
            # may result in negative values; handle it client-side
            r.hincrby(exp_key, item, 1 if bid else -1)
            r.expire(exp_key, 3600)
        else:
            unsaved_bids = get_unsaved_bids(experiment, exp_key)
            unsaved_bids[item] = 1 if bid else 0
            r.hmset(exp_key, unsaved_bids)

        session.events.create(event_type='item_bid' if bid else 'item_unbid',
                              data=data)
        p[exp_key].trigger('item-bid', data)
        return HttpResponse(json.dumps({'result': True}),
                            content_type='application/javascript')

    return HttpResponseBadRequest()
