from django import template

register = template.Library()


@register.filter()
def multiplystr(value, multiplier):
    return int(str(int(float(value) * float(multiplier)))[:-1] + '9')
