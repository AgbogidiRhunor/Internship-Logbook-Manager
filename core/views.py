from django.shortcuts import render, redirect


def landing(request):
    """
    Public landing page.
    Authenticated users are redirected directly to their dashboard.
    """
    # if request.user.is_authenticated:
    #     return redirect('dashboard:home')
    return render(request, 'landing/landing.html')


def error_400(request, exception=None):
    return render(request, 'errors/400.html', status=400)


def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def error_429(request, exception=None):
    return render(request, 'errors/429.html', status=429)


def error_500(request):
    return render(request, 'errors/500.html', status=500)