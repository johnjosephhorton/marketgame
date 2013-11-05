import random
import logging
from django.core.mail import send_mass_mail
from django.utils.timezone import now
from django.utils.formats import date_format

from experiments.models import Experiment, Winner


log = logging.getLogger(__name__)

EMAIL_SUBJECT_TEMPLATE = 'Market Game invitation'
EMAIL_MSG_TEMPLATE = """
Hi {participant_name},

You have been invited to participate in Market Game. To participate, use the following link:
{url}

The deadline for completion is {deadline} UTC, after which the link above expires.

Regards,

{contact_name}
"""
EMAIL_APP_URL = 'http://marketgame.herokuapp.com/exp/'


def get_email_message(session_participant):
    participant = session_participant.participant
    experiment = session_participant.experiment
    access_token = session_participant.access_token
    context = {
        'participant_name': participant.name,
        'contact_name': experiment.contact_name,
        'deadline': date_format(experiment.deadline, 'DATETIME_FORMAT'),
        'url': EMAIL_APP_URL+access_token+'/'
    }
    message = EMAIL_MSG_TEMPLATE.format(**context)
    subject = EMAIL_SUBJECT_TEMPLATE.format(**context)
    from_email = experiment.contact_email

    return subject, message, from_email, [participant.email]


def send_participants_emails(experiment_ids):
    experiments = Experiment.objects.in_bulk(experiment_ids)
    messages = []
    for experiment in experiments.values():
        if not experiment.started and not experiment.finished:
            for session in experiment.sessions.all():
                messages.append(get_email_message(session))
                session.has_emailed = True
                session.save()
            experiment.started = True
            experiment.active = True
            experiment.started_time = now()
            experiment.save()
            log.info('starting experiment {}'.format(experiment.short_name))
        else:
            log.error('experiment {} already started/finished'.format(experiment.short_name))

    send_mass_mail(messages, fail_silently=True)


def resend_participant_emails(experiment_ids):
    experiments = Experiment.objects.in_bulk(experiment_ids)
    messages = []
    for experiment in experiments.values():
        if (experiment.started and
            experiment.active and not experiment.finished):
            for session in experiment.sessions.all():
                if not session.has_completed:
                    messages.append(get_email_message(session))
                    session.has_emailed = True
                    session.save()
                    log.info('sending email to participant {}'.format(session.participant.name))
                else:
                    log.error('participant {} has already completed experiment'.format(session.participant.name))
        else:
            log.error('experiment {} is not active or finished'.format(experiment.short_name))

    send_mass_mail(messages, fail_silently=True)


def pick_winners(experiment_ids):
    experiments = Experiment.objects.in_bulk(experiment_ids).values()
    for e in experiments:
        items = e.items.all()
        random.seed()
        for item in items:
            selection = e.sessions.filter(choice_set__choices__item=item, choice_set__choices__bid=True)
            if len(selection) > 0:
                winner = random.choice(selection)
                Winner.objects.create(session=winner,
                                      experiment=e,
                                      participant=winner.participant,
                                      item=item)
                log.info('winner {} selected for item {}'.format(winner.participant, item.name))
