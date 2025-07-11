from django import template
from django.conf import settings

from importlib import import_module


register = template.Library()


@register.simple_tag
def settings_value(name, app_name='', **kwargs):
    if app_name:
        try:
            settings_file = import_module(f"{app_name}.settings")
        except ModuleNotFoundError:
            settings_file = settings
    else:
        settings_file = settings
    value = getattr(settings_file, name, None)
    if value and kwargs:
        return value.format(**kwargs)
    return value


@register.filter
def to_range(value, start=1):
    return range(start, value)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
