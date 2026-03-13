from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Doctor, Patient, Appointment, Clinic, Education, Experience,TimeSlot,Service,Award,Review, DoctorListing,Speciality, SubmitReview
from django.utils.html import mark_safe

# admin.py
from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Sum
from .models import Appointment, Doctor, Patient, Clinic

from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from datetime import datetime
import json

from .models import Appointment, Doctor, Patient


class CustomAdminSite(admin.AdminSite):
    site_header = "Clinic Super Admin"

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path('analytics/', self.admin_view(self.analytics_dashboard)),
        ]

        return custom_urls + urls

    def analytics_dashboard(self, request):

        appointments = Appointment.objects.select_related(
            "doctor", "doctor__user"
        )

        # KPI
        total_revenue = appointments.aggregate(
            total=Sum("total_amount")
        )["total"] or 0

        total_appointments = appointments.count()
        total_doctors = Doctor.objects.count()
        total_patients = Patient.objects.count()

        # MONTHLY REVENUE
        monthly_data = (
            appointments
            .annotate(month=TruncMonth("appointment_datetime"))
            .values("month")
            .annotate(total=Sum("total_amount"))
            .order_by("month")
        )

        months = []
        monthly_revenue = []

        for m in monthly_data:
            months.append(m["month"].strftime("%b"))
            monthly_revenue.append(float(m["total"]))

        # DOCTOR REVENUE
        doctor_data = (
            appointments
            .values("doctor__user__first_name")
            .annotate(total=Sum("total_amount"))
            .order_by("-total")
        )

        doctor_names = []
        doctor_revenue = []

        for d in doctor_data:
            doctor_names.append(d["doctor__user__first_name"])
            doctor_revenue.append(float(d["total"]))

        # RECENT PATIENTS
        recent_patients = Patient.objects.order_by("-id")[:5]

        context = dict(
            self.each_context(request),

            total_revenue=total_revenue,
            total_appointments=total_appointments,
            total_doctors=total_doctors,
            total_patients=total_patients,

            appointments=appointments[:10],

            months=json.dumps(months),
            monthly_revenue=json.dumps(monthly_revenue),

            doctor_names=json.dumps(doctor_names),
            doctor_revenue=json.dumps(doctor_revenue),

            recent_patients=recent_patients
        )

        return TemplateResponse(
            request,
            "admin/analytics_dashboard.html",
            context
        )


admin_site = CustomAdminSite(name="custom_admin")

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = (
        'email', 'first_name', 'last_name',
        'is_clinic', 'is_doctor', 'is_patient', 'is_staff', 'is_superuser'
    )
    list_filter = (
        'is_clinic', 'is_doctor', 'is_patient', 'is_staff', 'is_superuser'
    )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Role Flags', {'fields': ('is_clinic', 'is_doctor', 'is_patient')}),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'password1', 'password2',
                'is_clinic', 'is_doctor', 'is_patient', 'is_active', 'is_staff', 'is_superuser'
            )
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)



class DoctorAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'specialization', 'mobile_number', 'city', 'created_at', 'get_clinics')
    search_fields = ('user__first_name', 'user__last_name', 'specialization', 'city')
    list_filter = ('specialization', 'city')

    def get_clinics(self, obj):
        from doctorsapp.models import Clinic       
        owned = Clinic.objects.filter(doctor=obj)
        assigned = obj.clinics.all()
        all_clinics = set(owned) | set(assigned)

        if all_clinics:
            return ", ".join([clinic.name for clinic in all_clinics])
        return "-"
    
    get_clinics.short_description = 'Clinics'



class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'gender', 'age', 'blood_group', 'mobile_number', 'doctor','profile_image_preview') 
    search_fields = ('full_name', 'mobile_number', 'email', 'doctor__username', 'date_of_birth')
    list_filter = ('gender', 'blood_group')
    def profile_image_preview(self, obj):
        if obj.profile_image:
            return mark_safe(f'<img src="{obj.profile_image.url}" width="50" height="50" />')
        return "-"
    profile_image_preview.short_description = 'Profile Image'


class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient', 'appointment_datetime', 'appointment_type', 'status')
    list_filter = ('status', 'appointment_type')
    search_fields = ('doctor__user__first_name', 'patient__user__first_name')

class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'doctor', 'address', 'get_doctors')
    search_fields = ('name', 'doctor__user__first_name', 'doctor__user__last_name')
    list_filter = ('doctor',)
    ordering = ('name',)
    autocomplete_fields = ['doctor']

    def get_doctors(self, obj):
  
        if obj.doctor:
            return obj.doctor.get_full_name()
        return ''


class EducationAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'degree', 'institute', 'passing_year')
    search_fields = ('degree', 'institute')

class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'hospital_name', 'designation', 'from_date', 'to_date')
    search_fields = ('hospital_name', 'designation')

class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('day_of_week', 'doctor')
    search_fields = ('doctor__user__username',)

class DoctorListingAdmin(admin.ModelAdmin):
    list_display = ('get_doctor_name', 'treatment', 'price')

    def get_doctor_name(self, obj):
        return obj.doctor.get_full_name()
    get_doctor_name.short_description = 'Doctor Name'  


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'name', 'price')
    search_fields = ('doctor__user__first_name', 'name')


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'patient', 'rating', 'created_at')


class AwardAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'name','year',)

class SpecialitiesAdmin(admin.ModelAdmin):
    list_display = ('name',)

class SubmitReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'doctor', 'rating', 'name', 'email', 'created_at')
    list_filter = ('doctor', 'rating', 'created_at')
    search_fields = ('title', 'name', 'email', 'message')
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('doctor', 'rating', 'title', 'name', 'email', 'message', 'terms_accepted')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

admin_site.register(User, UserAdmin)
admin_site.register(Doctor, DoctorAdmin)
admin_site.register(Patient, PatientAdmin)
admin_site.register(Appointment, AppointmentAdmin)
admin_site.register(Clinic, ClinicAdmin)
admin_site.register(Education, EducationAdmin)
admin_site.register(Experience, ExperienceAdmin)
admin_site.register(DoctorListing, DoctorListingAdmin)
admin_site.register(Service, ServiceAdmin)
admin_site.register(TimeSlot, TimeSlotAdmin)
admin_site.register(Review, ReviewAdmin)
admin_site.register(Award, AwardAdmin)
admin_site.register(Speciality, SpecialitiesAdmin)
admin_site.register(SubmitReview, SubmitReviewAdmin)




