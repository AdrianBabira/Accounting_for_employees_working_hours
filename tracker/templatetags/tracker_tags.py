from django import template

register = template.Library()


@register.filter
def duration(seconds):
    hours, remainder = divmod(int(seconds), 3600)
    minutes = remainder // 60
    return f"{hours} ч {minutes:02} мин"
