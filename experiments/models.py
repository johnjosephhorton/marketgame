from django.db import models

from django_extensions.db.models import TimeStampedModel
from django_extensions.db.fields.json import JSONField


class Experiment(TimeStampedModel):
    short_name = models.CharField(max_length=40,
                                  unique=True,
                                  db_index=True)
    show_bid_counts = models.BooleanField(default=False)
    participants = models.ManyToManyField('Participant',
                                          through='Session',
                                          related_name='experiments')


class Participant(TimeStampedModel):
    name = models.CharField(max_length=80,
                            unique=True,
                            db_index=True)
    email = models.EmailField(max_length=254,
                              unique=True,
                              db_index=True)


class Session(TimeStampedModel):
    experiment = models.ForeignKey(Experiment, related_name='sessions')
    participant = models.ForeignKey(Participant, related_name='sessions')
    quota = models.PositiveSmallIntegerField(default=1)
    has_emailed = models.BooleanField(default=False)
    has_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('experiment', 'participant')


class Event(TimeStampedModel):
    session = models.ForeignKey(Session, related_name='events')
    event_type = models.CharField(max_length=80)
    data = JSONField(default='{}')


class Item(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)


class ChoiceSet(TimeStampedModel):
    session = models.ForeignKey(Session)
    order = JSONField(default='{}')


class Choice(TimeStampedModel):
    choice_set = models.ForeignKey(ChoiceSet, related_name='choices')
    item = models.ForeignKey(Item)
    bid = models.BooleanField(default=False)


class Winner(TimeStampedModel):
    session = models.ForeignKey(Session)
    experiment = models.ForeignKey(Experiment, related_name='winners')
    participant = models.ForeignKey(Participant)
    item = models.ForeignKey(Item)

    class Meta:
        unique_together = ('experiment', 'participant', 'item')
