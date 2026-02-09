from django import template

register = template.Library()

@register.filter
def times(number):
    """Repeat for a given number"""
    try:
        return range(int(number))
    except:
        return []


from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})