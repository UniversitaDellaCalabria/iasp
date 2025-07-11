from django.urls import path

from . views import *


app_name = 'calls'


urlpatterns = [
    path('calls/', calls, name='calls'),
    path('calls/<int:pk>/', call, name='call'),
]
