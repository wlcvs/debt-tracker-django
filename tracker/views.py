from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views.decorators.http import require_POST


class AppLoginView(LoginView):
    template_name = "tracker/login.html"
    redirect_authenticated_user = True


@require_POST
def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    from django.shortcuts import render
    return render(request, "tracker/dashboard.html")
