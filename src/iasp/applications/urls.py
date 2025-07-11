from django.urls import path

from . views import *


app_name = 'applications'


urlpatterns = [
    path('applications/', applications, name='applications'),
    path('applications/new/<int:call_pk>/', application_new, name='application_new'),

    path('applications/<int:application_pk>/', application, name='application'),
    path('applications/<int:application_pk>/edit/', application_edit, name='application_edit'),
    path('applications/<int:application_pk>/delete/', application_delete, name='application_delete'),
    path('applications/<int:application_pk>/submit/', application_submit, name='application_submit'),

    path('applications/<int:application_pk>/required/', application_required_list, name='application_required_list'),
    path('applications/<int:application_pk>/required/<int:teaching_id>/', application_required, name='application_required'),
    path('applications/<int:application_pk>/required/<int:teaching_id>/new/', application_required_new, name='application_required_new'),
    path('applications/<int:application_pk>/required/<int:teaching_id>/edit/<int:insertion_pk>/', application_required_edit, name='application_required_edit'),
    path('applications/<int:application_pk>/required/<int:insertion_pk>/delete/', application_required_delete, name='application_required_delete'),

    path('applications/<int:application_pk>/free/<int:year>/', application_free, name='application_free'),
    path('applications/<int:application_pk>/free/<int:year>/new/', application_free_new, name='application_free_new'),
    path('applications/<int:application_pk>/free/<int:year>/edit/<int:insertion_pk>/', application_free_edit, name='application_free_edit'),
    path('applications/<int:application_pk>/free/<int:insertion_pk>/delete/', application_free_delete, name='application_free_delete'),

    path('applications/<int:application_pk>/download/exams-certificate/', download_exams_certificate, name='download_exams_certificate'),
    path('applications/<int:application_pk>/download/teaching-plan/', download_teaching_plan, name='download_teaching_plan'),
    path('applications/<int:application_pk>/download/votes-conversion/', download_votes_conversion, name='download_votes_conversion'),
    path('applications/<int:application_pk>/download/language-certification/', download_language_certification, name='download_language_certification'),
    path('applications/<int:application_pk>/download/declaration-of-value/', download_declaration_of_value, name='download_declaration_of_value'),
    path('applications/<int:application_pk>/download/payment-receipt/', download_payment_receipt, name='download_payment_receipt'),
    path('applications/<int:application_pk>/insertion/<int:insertion_pk>/download/', download_insertion_attachment, name='download_insertion_attachment'),
]
