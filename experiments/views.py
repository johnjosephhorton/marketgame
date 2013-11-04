import pusher
from django.shortcuts import render, redirect, get_object_or_404
from django.template.response import TemplateResponse
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
