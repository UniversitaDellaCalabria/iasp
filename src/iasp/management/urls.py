from django.urls import path

from . views import *


app_name = 'management'

prefix = app_name

urlpatterns = [
    path(f'{prefix}/<str:structure_code>/', calls, name='calls'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/', call, name='call'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/', applications, name='applications'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/', application, name='application'),

    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/required/', application_required_list, name='application_required_list'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/required/<int:teaching_id>/', application_required, name='application_required'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/required/<int:teaching_id>/edit/<int:insertion_pk>/', application_required_detail, name='application_required_detail'),

    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/free/<int:year>/', application_free, name='application_free'),
    path(f'{prefix}/<str:structure_code>/call/<int:call_pk>/applications/<int:application_pk>/free/<int:year>/detail/<int:insertion_pk>/', application_free_detail, name='application_free_detail'),
]
