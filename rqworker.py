import os
import logging

import redis
from rq import Worker, Queue, Connection

from django.conf import settings

logging.basicConfig(level=logging.INFO)

listen = ['high', 'default', 'low']
logging.info('rqworker connecting to {}'.format(settings.REDIS_URL))
conn = redis.from_url(settings.REDIS_URL)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
