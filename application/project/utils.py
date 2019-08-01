import logging
import time

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

log = logging.getLogger(__name__)


def run_retrying_connect_to_db():
    logging.basicConfig(level=logging.DEBUG)
    db_conn = connections['default']

    counter = 0

    conn_exception = Exception('Can not connect to db')
    while counter < settings.COUNT_TRIES_CONNECT:
        log.info('Try connect to DB: %s', counter)
        try:
            return db_conn.cursor()
        except OperationalError as e:
            conn_exception = e
        counter += 1
        time.sleep(settings.SLEEP_TIME)

    raise conn_exception
