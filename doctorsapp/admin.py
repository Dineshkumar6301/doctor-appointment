from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Doctor, Patient, Appointment, Clinic, Education, Experience,TimeSlot,Service,Award,Review, DoctorListing,Speciality, SubmitReview
from django.utils.html import mark_safe


class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'first_name', 'last_name', 'is_doctor', 'is_patient', 'is_staff')
    list_filter = ('is_doctor', 'is_patient', 'is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_doctor', 'is_patient', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_doctor', 'is_patient', 'is_active', 'is_staff')}
        ),
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


admin.site.register(User, UserAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Clinic, ClinicAdmin)
admin.site.register(Education, EducationAdmin)
admin.site.register(Experience, ExperienceAdmin)
admin.site.register(DoctorListing, DoctorListingAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(TimeSlot, TimeSlotAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Award,  AwardAdmin)
admin.site.register(Speciality,SpecialitiesAdmin)
admin.site.register(SubmitReview,SubmitReviewAdmin)
