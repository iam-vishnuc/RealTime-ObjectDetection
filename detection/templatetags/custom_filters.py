import os
from django import template

register = template.Library()

@register.filter
def basename(value):
    """Extracts the base name of a file path."""
    return os.path.basename(value)
