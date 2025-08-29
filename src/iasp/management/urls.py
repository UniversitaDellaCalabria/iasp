from django.urls import path

from . views import commissions, structures


app_name = 'management'

prefix = app_name

urlpatterns = [
    # commissions
    path(f'{prefix}/commissions/', commissions.list, name='commissions'),
    path(f'{prefix}/commissions/call/<int:call_pk>/', commissions.detail, name='commission'),
    path(f'{prefix}/commissions/call/<int:call_pk>/applications/', commissions.applications, name='commission_applications'),
    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/', commissions.application, name='commission_application'),

    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/required/', commissions.application_required_list, name='commission_application_required_list'),
    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/required/<int:teaching_id>/', commissions.application_required, name='commission_application_required'),
    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/required/<int:teaching_id>/detail/<int:insertion_pk>/', commissions.application_required_detail, name='commission_application_required_detail'),
    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/required/<int:teaching_id>/logs/<int:insertion_pk>/', commissions.application_required_review_logs, name='commission_application_required_review_logs'),

    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/free/<int:year>/', commissions.application_free, name='commission_application_free'),
    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/free/<int:year>/detail/<int:insertion_pk>/', commissions.application_free_detail, name='commission_application_free_detail'),
    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/free/<int:year>/logs/<int:insertion_pk>/', commissions.application_free_review_logs, name='commission_application_free_review_logs'),

    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/required/<int:teaching_id>/review/<int:insertion_pk>/', commissions.application_required_review, name='commission_application_required_review'),
    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/required/<int:teaching_id>/review/<int:insertion_pk>/delete/', commissions.application_required_review_delete, name='commission_application_required_review_delete'),

    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/free/<int:year>/review/<int:insertion_pk>/', commissions.application_free_review, name='commission_application_free_review'),
    path(f'{prefix}/commissions/call/<int:call_pk>/applications/<int:application_pk>/free/<int:year>/review/<int:insertion_pk>/delete/', commissions.application_free_review_delete, name='commission_application_free_review_delete'),

    # structures
    path(f'{prefix}/<str:structure_code>/', structures.calls, name='calls'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/', structures.call, name='call'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/', structures.applications, name='applications'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/', structures.application, name='application'),

    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/required/', structures.application_required_list, name='application_required_list'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/required/<int:teaching_id>/', structures.application_required, name='application_required'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/required/<int:teaching_id>/edit/<int:insertion_pk>/', structures.application_required_detail, name='application_required_detail'),

    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/free/<int:year>/', structures.application_free, name='application_free'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/free/<int:year>/detail/<int:insertion_pk>/', structures.application_free_detail, name='application_free_detail'),
]
