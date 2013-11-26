from django import template

register = template.Library()


@register.filter
def percent(value, arg):
    return int(100 * value / arg)