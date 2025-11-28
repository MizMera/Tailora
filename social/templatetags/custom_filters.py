from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get value from dictionary by key"""
    if not dictionary:
        return None
    key_str = str(key)
    return dictionary.get(key_str)