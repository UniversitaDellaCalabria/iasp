from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from calls.models import Call

from management.settings import VIEW_APPLICATIONS_OFFICE

from . models import (OrganizationalStructure,
                      OrganizationalStructureOfficeEmployee)


def is_operator(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        if request.user.is_superuser:
            return func_to_decorate(*original_args, **original_kwargs)
        my_offices = OrganizationalStructureOfficeEmployee.objects\
                                                          .filter(employee=request.user,
                                                                  office__is_active=True,
                                                                  office__organizational_structure__is_active=True)
        if not my_offices.exists():
            raise PermissionDenied
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func


def is_structure_operator(func_to_decorate):
    """
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        structure = get_object_or_404(OrganizationalStructure,
                                      unique_code=original_kwargs.get(
                                          'structure_code', None),
                                      is_active=1)
        original_kwargs['structure'] = structure
        if request.user.is_superuser:
            return func_to_decorate(*original_args, **original_kwargs)
        my_offices = OrganizationalStructureOfficeEmployee.objects\
                                                          .filter(employee=request.user,
                                                                  office__is_active=True,
                                                                  office__name=VIEW_APPLICATIONS_OFFICE,
                                                                  office__organizational_structure_id=structure.pk)\
                                                          .values_list('office__name', flat=True)
        if not my_offices.exists():
            raise PermissionDenied
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func


def can_manage_call(func_to_decorate):
    """
    """
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        call = get_object_or_404(
            Call,
            is_active=True,
            pk=original_kwargs['call_pk'],
            course_json_it__isnull=False,
        )
        if not call.course_json_it.get('DepartmentCod', '') == original_kwargs['structure_code']:
            raise PermissionDenied
        original_kwargs['call'] = call
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func
