"""
URL configuration for iasp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include

from generics.settings import ADMIN_PATH


urlpatterns = [
    path(f'{ADMIN_PATH}/', admin.site.urls),
]

urlpatterns += path('', include('accounts.urls', namespace='accounts')),
urlpatterns += path('', include('generics.urls', namespace='generics')),
urlpatterns += path('', include('calls.urls', namespace='calls')),
urlpatterns += path('', include('applications.urls', namespace='applications')),
urlpatterns += path('', include('management.urls', namespace='management')),

if 'saml2_sp' in settings.INSTALLED_APPS:
    from djangosaml2 import views

    urlpatterns += path('{}/login/'.format(settings.SAML2_URL_PREFIX),
                        views.LoginView.as_view(), name='login'),
    urlpatterns += path('{}/acs/'.format(settings.SAML2_URL_PREFIX),
                        views.AssertionConsumerServiceView.as_view(), name='saml2_acs'),
    urlpatterns += path('{}/logout/'.format(settings.SAML2_URL_PREFIX),
                        views.LogoutInitView.as_view(), name='logout'),
    urlpatterns += path('{}/ls/'.format(settings.SAML2_URL_PREFIX),
                        views.LogoutView.as_view(), name='saml2_ls'),
    urlpatterns += path('{}/ls/post/'.format(settings.SAML2_URL_PREFIX),
                        views.LogoutView.as_view(), name='saml2_ls_post'),
    urlpatterns += path('{}/metadata/'.format(settings.SAML2_URL_PREFIX),
                        views.MetadataView.as_view(), name='saml2_metadata'),

else:
    urlpatterns += path('{}/login/'.format(settings.LOCAL_URL_PREFIX),
                        LoginView.as_view(template_name='login.html'),
                        name='login'),
    urlpatterns += path('{}/logout/'.format(settings.LOCAL_URL_PREFIX),
                        LogoutView.as_view(template_name='logout.html', next_page='/'),
                        name='logout'),
