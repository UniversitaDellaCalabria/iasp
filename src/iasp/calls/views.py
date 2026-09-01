from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from . models import *


@login_required
def calls(request):
    template = 'calls.html'
    calls = Call.get_active(user=request.user)
    return render(request, template, {'calls': calls})


@login_required
def call(request, pk):
    template = 'call.html'
    call = get_object_or_404(
        Call,
        pk=pk
    )

    # bando scaduto
    if not call.is_in_progress():
        messages.add_message(request, messages.ERROR, _('Expired call'))
        return redirect('calls:calls')

    # bando non pubblico e utente non abilitato
    if not call.user_is_enabled(user=request.user):
        messages.add_message(request, messages.ERROR, _('You are not eligible to participate in this call'))
        return redirect('calls:calls')
    
    return render(
        request,
        template,
        {'call': call}
    )
