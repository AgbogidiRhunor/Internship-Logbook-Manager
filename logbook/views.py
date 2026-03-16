from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.db.models import Q

from .models import DailyLogEntry
from .forms import DailyLogEntryForm


def _student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_student:
            return HttpResponseForbidden('Access denied.')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@_student_required
def log_list(request):
    entries = DailyLogEntry.objects.filter(student=request.user)

    month = request.GET.get('month')
    week = request.GET.get('week')
    day = request.GET.get('day')

    if month:
        entries = entries.filter(internship_month=month)
    if week:
        entries = entries.filter(internship_week=week)
    if day:
        entries = entries.filter(day_of_week=day)

    profile = request.user.student_profile
    months_range = range(1, int(profile.internship_duration) + 1)
    weeks_range = range(1, (int(profile.internship_duration) * 4) + 2)

    from .models import DayOfWeek
    return render(request, 'logbook/log_list.html', {
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
        request.POST or None,
        request.FILES or None,
        student_user=request.user,
    )

    if request.method == 'POST':
        form.instance.student = request.user
        if form.is_valid():
            entry = form.save()
            messages.success(request, f'Log entry for {entry.entry_date} saved.')
            return redirect('logbook:log_list')

    return render(request, 'logbook/log_form.html', {'form': form, 'action': 'Create'})


@login_required
@_student_required
def log_edit(request, pk):
    entry = get_object_or_404(DailyLogEntry, pk=pk)
    # Scope: student can only edit their own entries
    if entry.student_id != request.user.pk:
        return HttpResponseForbidden('You cannot edit another student\'s log.')

    form = DailyLogEntryForm(
        request.POST or None,
        request.FILES or None,
        instance=entry,
        student_user=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Log entry updated.')
        return redirect('logbook:log_list')
    return render(request, 'logbook/log_form.html', {'form': form, 'action': 'Edit', 'entry': entry})


@login_required
@_student_required
def log_delete(request, pk):
    entry = get_object_or_404(DailyLogEntry, pk=pk)
    if entry.student_id != request.user.pk:
        return HttpResponseForbidden('Access denied.')
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'Log entry deleted.')
        return redirect('logbook:log_list')
    return render(request, 'logbook/log_confirm_delete.html', {'entry': entry})


@login_required
@_student_required
def log_detail(request, pk):
    entry = get_object_or_404(DailyLogEntry, pk=pk)
    if entry.student_id != request.user.pk:
        return HttpResponseForbidden('Access denied.')
    return render(request, 'logbook/log_detail.html', {'entry': entry})
