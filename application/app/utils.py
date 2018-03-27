from django.utils import timezone
import pytz
from project import settings


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
