from .models import Clinic

def clinic_global(request):
    clinic = None

    if request.user.is_authenticated and getattr(request.user, "is_clinic", False):
        clinic = Clinic.objects.filter(admin=request.user).first()

    return {
        "clinic": clinic
    }