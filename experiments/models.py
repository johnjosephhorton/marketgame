import uuid
from django.db import models

from django_extensions.db.models import TimeStampedModel
from django_extensions.db.fields.json import JSONField


class Experiment(TimeStampedModel):
    short_name = models.CharField(max_length=40,
                                  unique=True,
                                  db_index=True)
    show_bid_counts = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    deadline = models.DateTimeField()
    participants = models.ManyToManyField('Participant',
                                          through='Session',
                                          related_name='experiments')
    items = models.ManyToManyField('Item', related_name='experiments')

    contact_name = models.CharField(max_length=80)
    contact_email = models.EmailField(max_length=254)

    started = models.BooleanField(default=False, editable=False)
    started_time = models.DateTimeField(null=True, blank=True, editable=False)
    finished = models.BooleanField(default=False, editable=False)
    finished_time = models.DateTimeField(null=True, blank=True, editable=False)

    def __unicode__(self):
        return self.short_name

    def is_active(self):
        return self.active and self.started and not self.finished


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
    access_token = models.CharField(max_length="32",
                                    unique=True,
                                    db_index=True,
                                    editable=False)
    experiment = models.ForeignKey(Experiment, related_name='sessions')
    participant = models.ForeignKey(Participant, related_name='sessions')
    quota = models.PositiveSmallIntegerField(default=1)
    has_emailed = models.BooleanField(default=False)
    has_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('experiment', 'participant')

    def __unicode__(self):
        return 'Session {}'.format(self.id)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.access_token = uuid.uuid1().hex
        return super(Session, self).save(*args, **kwargs)


class Event(TimeStampedModel):
    EVENT_TYPE_CHOICES = (
        ('exp_started', 'Experiment started'),
        ('exp_finished', 'Experiment finished'),
        ('item_bid', 'Item bid'),
        ('item_unbid', 'Item unbid')
    )
    session = models.ForeignKey(Session, related_name='events')
    event_type = models.CharField(max_length=80, choices=EVENT_TYPE_CHOICES)
    data = JSONField(default='{}')

    def __unicode__(self):
        return 'Event {}'.format(self.id)


class Item(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __unicode__(self):
        return '{} | {}'.format(self.name, self.amount)


class ChoiceSet(TimeStampedModel):
    session = models.OneToOneField(Session, related_name='choice_set')
    order = JSONField(default='[]')

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
