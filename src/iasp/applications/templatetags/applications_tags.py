from django import template


register = template.Library()


@register.simple_tag
def is_editable(application, user):
    return application.is_editable(user=user)


@register.simple_tag
def is_submittable(application, user):
    return application.is_submittable(user=user)