import pusher
import redis
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.template.response import TemplateResponse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.utils.timezone import now
from django.conf import settings
from django.contrib import messages
from django import forms

from experiments.models import (Experiment,
                                ChoiceSet,
                                Choice,
                                Item,
                                Session)
from experiments.forms import BiddingForm


def get_bidding_form(experiment):
    form = BiddingForm()

    for item in experiment.items.all():
        data_attrs = {
            'data-amount': str(item.amount),
            'data-saved-bids': '1',
        }
        form.fields[item.name] = forms.BooleanField(required=False,
                                                    widget=forms.CheckboxInput(attrs=data_attrs))
    return form


def index(request, access_token=None):
    if access_token is None:
        return redirect('home')

    session = get_object_or_404(Session, access_token=access_token)
    experiment = session.experiment

    # deadline check
    if now() >= experiment.deadline and not experiment.finished:
        experiment.finished = True
        experiment.finished_time = now()
        # queue pick-winners background job
        messages.add_message(request,
                             messages.ERROR,
                             'Your session has already expired.', extra_tags='alert-danger')
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
        pass
    else:
        # check if session is valid and experiment active
        if experiment.is_active and not session.has_completed:
            return render(request, 'experiments/index.html', context)
        else:
            # redirect
            messages.add_message(request,
                                 messages.ERROR,
                                 'Your session has already expired.', extra_tags='alert-danger')
            redirect('home')


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

        p[exp_key].trigger('item-bid', data)
        return HttpResponse(json.dumps({'result': True}),
                            content_type='application/javascript')
    else:
        return HttpResponseBadRequest()

    return HttpResponseBadRequest()
