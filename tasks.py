import logging

from experiments.models import Experiment


log = logging.getLogger(__name__)


def send_participants_emails(experiment_name):
    experiment = Experiment.objects.get(short_name=experiment_name)
    if not experiment.started:
        log.info('starting experiment {}'.format(experiment_name))
        # TODO send emails to participants
        experiment.started = True
        experiment.save()
    else:
        log.info('experiment {} already started'.format(experiment_name))
