import django_tables2 as tables

from django.utils.translation import gettext_lazy as _

from applications.models import Application


class ApplicationTable(tables.Table):
    user = tables.TemplateColumn(
        verbose_name=_("User"),
        template_code='''
        <a href="{% url 'management:application' structure.unique_code call.pk record.pk %}">
            {{ record.user }}
        </a>
        '''
    )
    submission_date = tables.Column(verbose_name=_("Submission date"))
    protocol_number = tables.Column(verbose_name=_("Registration number"))
    protocol_date = tables.Column(verbose_name=_("Registration date"))

    class Meta:
        model = Application
        template_name = "django_tables2/bootstrap5-responsive.html"
        fields = ("user", "submission_date", "protocol_number", "protocol_date")
        attrs = {"class": "table table-bordered table-striped table-hover"}
