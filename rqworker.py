import os
import logging

import redis
from rq import Worker, Queue, Connection

logging.basicConfig(level=logging.INFO)

listen = ['high', 'default', 'low']

redis_url = os.getenv('REDISCLOUD_URL', 'redis://localhost:6379')
conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(redis.Redis()):
        worker = Worker(map(Queue, listen))
        worker.work()
