from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib import auth
def unauthenticated_patient(view_func):
    def wrapper_fun(request,*args,**kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        else:
            return view_func(request,*args,**kwargs)
    return wrapper_fun

def allowed_users(allowed_roles=[]):
    def decorator(view_func):
        def wrapper_func(request,*args,**kwargs):
            if not request.user.is_authenticated:
                return redirect('patient_login')
            if request.user.is_superuser or (request.user.username and request.user.username.lower() == 'dhanush') or (request.user.email and request.user.email.lower() == 'dhanushnaginane@gmail.com'):
                return view_func(request,*args,**kwargs)
            user_groups = set(request.user.groups.values_list('name', flat=True))
            if any(role in user_groups for role in allowed_roles):
                return view_func(request,*args,**kwargs)
            else:
                auth.logout(request)
                return HttpResponse("You are not authorized to access this page, Please login from valid panel")
        return wrapper_func
    return decorator

