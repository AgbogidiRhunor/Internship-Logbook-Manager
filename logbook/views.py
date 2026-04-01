import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from accounts.views import _log_audit
from .models import DailyLogEntry
from .forms import DailyLogEntryForm

logger = logging.getLogger(__name__)

_ALLOWED_DAYS = {
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
}
_MAX_INTERNSHIP_MONTHS = 6
_MAX_INTERNSHIP_WEEKS = 26


def _student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_student:
            return HttpResponseForbidden('Access denied.')
        return view_func(request, *args, **kwargs)
    return wrapper


def _owned_entry(pk, user):
    entry = get_object_or_404(DailyLogEntry, pk=pk)
    if entry.student_id != user.pk:
        logger.warning('IDOR: user %s tried to access log entry %s', user.username, pk)
        _log_audit(user, 'idor_attempt_log_entry', 'DailyLogEntry', pk)
        return None, HttpResponseForbidden('You cannot access another student\'s log.')
    return entry, None


def _safe_int_param(value, min_val, max_val):
    try:
        parsed = int(value)
        if min_val <= parsed <= max_val:
            return str(parsed)
    except (ValueError, TypeError):
        pass
    return ''


@login_required
@_student_required
def log_list(request):
    entries = DailyLogEntry.objects.filter(student=request.user)
    month = _safe_int_param(request.GET.get('month', ''), 1, _MAX_INTERNSHIP_MONTHS)
    week  = _safe_int_param(request.GET.get('week', ''), 1, _MAX_INTERNSHIP_WEEKS)
    day   = request.GET.get('day', '').strip()
    if month:
        entries = entries.filter(internship_month=month)
    if week:
        entries = entries.filter(internship_week=week)
    if day not in _ALLOWED_DAYS:
        day = ''
    if day:
        entries = entries.filter(day_of_week=day)
    profile = request.user.student_profile
    months_range = range(1, int(profile.internship_duration) + 1)
    weeks_range  = range(1, (int(profile.internship_duration) * 4) + 2)
    from .models import DayOfWeek
    return render(request, 'pages/logbook/log_list.html', {
        'entries': entries.order_by('-entry_date'),
        'profile': profile,
        'months_range': months_range,
        'weeks_range': weeks_range,
        'day_choices': DayOfWeek.choices,
        'filter_month': month,
        'filter_week': week,
        'filter_day': day,
    })


@login_required
@_student_required
def log_create(request):
    form = DailyLogEntryForm(
        request.POST or None, request.FILES or None, student_user=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        entry = form.save(commit=False)
        entry.student = request.user
        entry.save()
        messages.success(request, f'Log entry for {entry.entry_date} saved.')
        return redirect('logbook:log_list')
    return render(request, 'pages/logbook/log_form.html', {'form': form, 'action': 'Create'})


@login_required
@_student_required
def log_edit(request, pk):
    entry, err = _owned_entry(pk, request.user)
    if err:
        return err
    form = DailyLogEntryForm(
        request.POST or None, request.FILES or None,
        instance=entry, student_user=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Log entry updated.')
        return redirect('logbook:log_list')
    return render(request, 'pages/logbook/log_form.html', {
        'form': form, 'action': 'Edit', 'entry': entry,
    })


@login_required
@_student_required
def log_delete(request, pk):
    entry, err = _owned_entry(pk, request.user)
    if err:
        return err
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Log entry deleted.')
        return redirect('logbook:log_list')
    return redirect('logbook:log_list')


@login_required
@_student_required
def log_detail(request, pk):
    entry, err = _owned_entry(pk, request.user)
    if err:
        return err
    return render(request, 'pages/logbook/log_detail.html', {'entry': entry})