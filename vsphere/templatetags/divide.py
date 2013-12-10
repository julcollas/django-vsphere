from django import template

register = template.Library()


@register.filter
def divide(value, arg):
    return "%.2f" % (value / float(arg))