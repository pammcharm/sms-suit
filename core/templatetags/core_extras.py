from django import template

register = template.Library()


@register.filter
def get_attr(obj, name):
    value = getattr(obj, name, '')
    if callable(value):
        value = value()
    return value
