from django import template
from django.db.models import Q

from organizational_area.models import *


register = template.Library()


@register.simple_tag
def is_operator(user):
    if not user:
        return []
    if user.is_superuser:
        return OrganizationalStructure.objects.filter(is_active=True).values('name', 'unique_code')
    user_offices = OrganizationalStructureOfficeEmployee.objects\
        .filter(employee=user,
                office__is_active=True,
                office__organizational_structure__is_active=True)
    if not user_offices.exists():
        return []
    structures = []
    for office in user_offices:
        if not office.office.organizational_structure in structures:
            structures.append(office.office.organizational_structure)
    return structures


@register.simple_tag
def employee_offices(user, structure=None):
    """
    Returns all user offices relationships
    """
    if not user:
        return None
    query = Q(employee=user)
    query_structure = ()
    if structure:
        query_structure = Q(office__organizational_structure=structure)
    return OrganizationalStructureOfficeEmployee.objects.filter(query,
                                                                query_structure)
