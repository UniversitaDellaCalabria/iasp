from django.urls import path

from . views import *


app_name = 'generics'


urlpatterns = [
    path('', home, name='home'),
]
