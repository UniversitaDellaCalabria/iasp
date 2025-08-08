import django_filters

from django.utils.translation import gettext_lazy as _

from applications.models import Application


class ApplicationFilter(django_filters.FilterSet):
    user__last_name = django_filters.CharFilter(label=_("User"), lookup_expr='icontains')
    protocol_number = django_filters.CharFilter(label=_("Registration number"), lookup_expr='icontains')
    # ~ protocol_date = django_filters.DateTimeFilter(lookup_expr='exact')

    class Meta:
        model = Application
        fields = ['user__last_name', 'protocol_number']
