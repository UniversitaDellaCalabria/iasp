from django.shortcuts import get_object_or_404

from applications.models import Application


def application_check(func_to_decorate):
    def new_func(*original_args, **original_kwargs):
        request = original_args[0]
        application = get_object_or_404(
            Application,
            call__pk=original_kwargs['call_pk'],
            pk=original_kwargs['application_pk'],
            submission_date__isnull=False
        )
        original_kwargs['application'] = application
        return func_to_decorate(*original_args, **original_kwargs)
    return new_func


# ~ def application_editable(func_to_decorate):
    # ~ def new_func(*original_args, **original_kwargs):
        # ~ request = original_args[0]
        # ~ application = original_kwargs['application']
        # ~ if not application.is_editable():
            # ~ messages.add_message(
                # ~ request,
                # ~ messages.ERROR,
                # ~ _('Unable to edit application')
            # ~ )
            # ~ return redirect(
                # ~ 'applications:application',
                # ~ application_pk=application.pk
            # ~ )
        # ~ return func_to_decorate(*original_args, **original_kwargs)
    # ~ return new_func


# ~ def activity_check(func_to_decorate):
    # ~ def new_func(*original_args, **original_kwargs):
        # ~ request = original_args[0]
        # ~ application = original_kwargs['application']
        # ~ teaching_id = original_kwargs['teaching_id']
        # ~ target_teaching = application.call.get_teaching_data(
            # ~ teaching_id,
            # ~ request.LANGUAGE_CODE
        # ~ )
        # ~ if target_teaching['modules']:
            # ~ messages.add_message(
                # ~ request,
                # ~ messages.ERROR,
                # ~ _('The activity is divided into modules. Request validation for each of them')
            # ~ )
            # ~ return redirect(
                # ~ 'applications:application_required_list',
                # ~ application_pk=application.pk
            # ~ )

        # ~ codes_to_exclude = CallExcludedActivity.objects.filter(
            # ~ call=application.call,
            # ~ is_active=True
        # ~ ).values_list('code', flat=True)

        # ~ if target_teaching['cod'] in codes_to_exclude:
            # ~ messages.add_message(
                # ~ request,
                # ~ messages.ERROR,
                # ~ _('It is not possible to request validation of credits for this activity')
            # ~ )
            # ~ return redirect(
                # ~ 'applications:application_required_list',
                # ~ application_pk=application.pk
            # ~ )

        # ~ original_kwargs['target_teaching'] = target_teaching
        # ~ return func_to_decorate(*original_args, **original_kwargs)
    # ~ return new_func
