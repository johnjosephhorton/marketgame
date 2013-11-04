import re
from django import forms
from django.contrib.admin import widgets

from experiments.models import Experiment


PARTICIPANTS_REGEX = re.compile(r'^[\w\s]+,[\w@\s\.]+,[\s\d]+$')
ITEMS_REGEX = re.compile(r'[\w\s]+,\s*\$?\d+\.?[\d{2}]?')


class QuickExperiment(forms.Form):
    short_name = forms.CharField(max_length=40,
                                 required=True,
                                 widget=widgets.AdminTextInputWidget,
                                 help_text='Short name for experiment, which will be used in URL.')
    contact_name = forms.CharField(max_length=80,
                                   required=True,
                                   widget=widgets.AdminTextInputWidget,
                                   help_text='Contact name to be shown to participants.')
    contact_email = forms.CharField(max_length=254,
                                    required=True,
                                    widget=widgets.AdminEmailInputWidget,
                                    help_text='Contact email to be shown to participants.')
    show_bid_counts = forms.BooleanField(initial=False, required=False,
                                         help_text='Show bid counts to participants.')
    start_on_create = forms.BooleanField(initial=False, required=False,
                                         help_text='Start experiment immediately.')
    deadline = forms.DateTimeField(widget=widgets.AdminSplitDateTime,
                                   help_text='Deadline for experiment active status.')
    participants = forms.CharField(widget=widgets.AdminTextareaWidget,
                                   label='Participants (w/ quota)',
                                   help_text='Line-separated particpant list, using format:\nname, email, quota')
    items = forms.CharField(widget=widgets.AdminTextareaWidget,
                            label='Items (w/ amount)',
                            help_text='Line-separated item list, using format:\nitem-name, amount')


    def clean_short_name(self):
        short_name = self.cleaned_data['short_name']
        if Experiment.objects.filter(short_name=short_name).exists():
            raise forms.ValidationError('This experiment already exists.', code='invalid')
        return short_name

    def clean_participants(self):
        participants = []
        for line in self.cleaned_data['participants'].split('\n'):
            # ignore empty lines
            if line:
                if PARTICIPANTS_REGEX.match(line):
                    name, email, quota = [w.strip() for w in line.split(',')]
                    try:
                        participants.append((name,email, int(quota, 10)))
                    except ValueError, e:
                        raise forms.ValidationError('"{}" please use a valid integer'.format(line))
                else:
                    raise forms.ValidationError('"{}" is not properly formatted.'.format(line))
        return participants

    def clean_items(self):
        items = []
        for line in self.cleaned_data['items'].split('\n'):
            # ignore empty lines
            if line:
                if ITEMS_REGEX.match(line):
                    name, amount = [w.strip() for w in line.split(',')]
                    try:
                        items.append((name, float(amount if '$' not in amount else amount[1:])))
                    except ValueError, e:
                        raise forms.ValidationError('"{}" please use a valid float or integer'.format(line))
                else:
                    raise forms.ValidationError('"{}" is not properly formatted'.format(line))
        return items
