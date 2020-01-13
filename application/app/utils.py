import logging
from functools import wraps
from time import sleep

import pytz
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import autoreload, timezone

log = logging.getLogger(__name__)


def use_timezone(date):
    """
    :param date: timezone.now (example)
    :return: localised time for country (in settings.DEFAULT_TIMEZONE)
    """
    # возможно, если в будушем будут чуваки из разных стран, это заменить на TIMEZONE другой страны
    default_tz = pytz.timezone(settings.DEFAULT_TIMEZONE)

    # timezone.activate(pytz.timezone(DEFAULT_TIMEZONE))
    # current_tz = timezone.get_current_timezone()
    # current_tz.normalize(date)

    return default_tz.normalize(date)


def get_datetime_now():
    return use_timezone(timezone.now())


def retry_if_false(attempts_count=3, sleep_time=0.5, use_logging=False):
    """ retry ryb function

    :param attempts_count: run function while func will not return boolean True
    :param sleep_time: time sleep in seconds

    example usage:

        @retry_if_false()
        def your_func(*args, **kwargs):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            for count in range(attempts_count):
                result = func(*args, **kwargs)
                if result:
                    return result
                if use_logging:
                    log.info('Retry count=%d func=%s', count, func.__name__)
                sleep(sleep_time)
            return False

        return wrap

    return decorator


def safe_str(obj):
    if isinstance(obj, str):
        return obj.encode('unicode_escape').decode('utf-8')
    if isinstance(obj, bytes):
        try:
            return obj.decode('utf-8')
        except UnicodeEncodeError:
            return obj.decode('ascii', 'ignore')
        except Exception:
            return ""
    return obj


class BaseCommandWithAutoreload(BaseCommand):
    def handle(self, *args, **options):
        autoreload.run_with_reloader(self.main)

    def main(self):
        pass
