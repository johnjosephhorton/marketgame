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

    def __unicode__(self):
        return self.short_name


class Participant(TimeStampedModel):
    name = models.CharField(max_length=80,
                            unique=True,
                            db_index=True)
    email = models.EmailField(max_length=254,
                              unique=True,
                              db_index=True)

    def __unicode__(self):
        return '{} <{}>'.format(self.name, self.email)


class Session(TimeStampedModel):
    experiment = models.ForeignKey(Experiment, related_name='sessions')
    participant = models.ForeignKey(Participant, related_name='sessions')
    quota = models.PositiveSmallIntegerField(default=1)
    has_emailed = models.BooleanField(default=False)
    has_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('experiment', 'participant')

    def __unicode__(self):
        return 'Session {}'.format(self.id)


class Event(TimeStampedModel):
    session = models.ForeignKey(Session, related_name='events')
    event_type = models.CharField(max_length=80)
    data = JSONField(default='{}')

    def __unicode__(self):
        return 'Event {}'.format(self.id)


class Item(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __unicode__(self):
        return self.name


class ChoiceSet(TimeStampedModel):
    session = models.ForeignKey(Session)
    order = JSONField(default='{}')

    def __unicode__(self):
        return 'ChoiceSet {}'.format(self.id)


class Choice(TimeStampedModel):
    choice_set = models.ForeignKey(ChoiceSet, related_name='choices')
    item = models.ForeignKey(Item)
    bid = models.BooleanField(default=False)

    def __unicode__(self):
        return 'Choice {}'.format(self.id)


class Winner(TimeStampedModel):
    session = models.ForeignKey(Session)
    experiment = models.ForeignKey(Experiment, related_name='winners')
    participant = models.ForeignKey(Participant)
    item = models.ForeignKey(Item)

    class Meta:
        unique_together = ('experiment', 'participant', 'item')

    def __unicode__(self):
        return 'Winner {}'.format(self.id)
