from django import template

register = template.Library()

@register.filter
def add_class(field, css_class):
    """Add CSS class to form field"""
    return field.as_widget(attrs={'class': css_class})

@register.filter
def get_choice_display(choice_value, choices):
    """Get display value for a choice field"""
    if not choice_value or not choices:
        return choice_value
    
    # Convert choices to dict if it's a list of tuples
    if isinstance(choices, (list, tuple)):
        choices_dict = dict(choices)
        return choices_dict.get(choice_value, choice_value)
    
    return choice_value
