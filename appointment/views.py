from django.shortcuts import redirect

def appointment(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='DOCTOR').exists():
            return redirect('appointment')
        elif request.user.groups.filter(name='PATIENT').exists():
            return redirect('view_appointment')
    return redirect('patient_login')
