import json
from django.shortcuts import render, redirect, get_object_or_404 
from django.urls import reverse
from django.http import JsonResponse ,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.contrib.auth import update_session_auth_hash
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, date, timedelta
import logging
from django.utils.timezone import now
from .models import User, Doctor, Patient, Appointment, Clinic, Education, Experience ,Message,ScheduleTiming,PatientSocialLinks,DoctorListing,Award,Speciality,SubmitReview
from .forms import DoctorProfileForm, ClinicForm, EducationForm, ExperienceForm,PatientForm,AppointmentForm,Service, AwardForm,SpecialityForm
from .models import FavouriteDoctor
from django.forms import  inlineformset_factory
from django.db.models import Value as V
from django.db.models.functions import Concat
from .models import  TimeSlot
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from. models import Conversation
from .forms import SocialLinksForm
from django.contrib.auth import get_user_model
from django.utils.timezone import make_aware
from .forms import TimeSlotForm
from .forms import SubmitReviewForm
from django.utils.dateparse import parse_time
from dateutil.relativedelta import relativedelta
from django.db.models import Avg
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode , urlsafe_base64_encode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from .models import Clinic, Branch
from .forms import BranchForm
from .models import GalleryImage
from django.http import HttpResponseForbidden
import re
from itertools import groupby

logger = logging.getLogger(__name__)
User = get_user_model() 
def is_ajax(request):
    """Helper function to check if the request is an AJAX request."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def home(request):
    doctor = None
    patient = None
    clinics = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                pass
    if request.user.is_authenticated and request.user.is_clinic:
        try:
           clinics = Clinic.objects.filter(doctor__user=request.user)
        except Clinic.DoesNotExist:
            pass

    doctors = Doctor.objects.filter(
    is_available=True
    ).order_by(
        '-is_featured',
        '-average_rating',
        '-review_count'
    )[:10]

    doctor_data = []

    for doc in doctors:
        experiences = doc.experience_set.all()

        exp_list = []
        for exp in experiences:
            duration = calculate_experience_years(exp.from_date, exp.to_date)
            exp_list.append({
                'hospital_name': exp.hospital_name,
                'designation': exp.designation,
                'from_date': exp.from_date,
                'to_date': exp.to_date,
                'duration': duration
            })

        doctor_data.append({
            'doctor': doc,
            'experiences': exp_list
        })
    context = {
        'doctor': doctor,
        'patient': patient,  
        'clinics':clinics,
        'doctors': doctors ,
        'doctor_data' : doctor_data,
        'patients_count': Patient.objects.count(),
        'doctors_count': Doctor.objects.count(),
        'clinics_count': Clinic.objects.count(),
    
    }
    return render(request, 'base.html', context)
User = get_user_model()
def register_view(request):
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None
        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None

    if request.method == 'GET':
        return render(request, 'register.html', {
            'doctor': doctor,
            'patient': patient,   
        })
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            password = data.get('password')
            confirm_password = data.get('confirm_password')
            mobile_number = data.get('phone')
            user_type = data.get('user_type')

            if password != confirm_password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Passwords do not match'
                })

            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Email already exists'
                })

            with transaction.atomic():
                user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    mobile_number=mobile_number,
                )

                if user_type == 'doctor':
                    user.is_doctor = True
                    user.save()
                    Doctor.objects.create(
                        user=user,
                        specialization=data.get('specialization', '')
                    )
                else:
                    user.is_patient = True
                    user.save()
                    Patient.objects.create(user=user)

                return JsonResponse({
                    'status': 'success',
                    'message': 'Registration successful',
                    'redirect': '/signin/'
                })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

@csrf_exempt
def login_view(request):
    doctor = None
    patient = None

    if request.user.is_authenticated:
        doctor = getattr(request.user, 'doctor_profile', None)
        patient = getattr(request.user, 'patient_profile', None)

    if request.method == 'GET':
        return render(request, 'login.html', {
            'doctor': doctor,
            'patient': patient,
        })

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            user = authenticate(request, username=email, password=password)

            if user:
                login(request, user)

                if hasattr(user, 'doctor_profile'):
                    user_type = 'doctor'

                elif hasattr(user, 'patient_profile'):
                    user_type = 'patient'

                elif getattr(user, 'is_clinic', False):
                    user_type = 'clinic'

                else:
                    user_type = 'unknown'

                return JsonResponse({
                    'status': 'success',
                    'message': 'Login successful',
                    'redirect': '/',
                    'user_type': user_type
                })

            return JsonResponse({
                'status': 'error',
                'message': 'Invalid email or password'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
def logout_view(request):
    logout(request)
    return redirect('home')                       

@login_required
def patient_dashboard_view(request):
  
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        return HttpResponse("Patient profile not found.", status=404)

    appointments = Appointment.objects.filter(
    patient=patient,
    payment_status="paid"
).select_related('doctor').order_by('-date')
    doctors = Doctor.objects.all()

    user_content_type = ContentType.objects.get_for_model(Patient)

    new_messages = Message.objects.filter(
        receiver_content_type=user_content_type,
        receiver_object_id=patient.id,
        is_read=False                                                                                                                                      
    ).count()

    upcoming_appointments = Appointment.objects.filter(
        patient=patient,
        appointment_datetime__gte=timezone.now()
    ).order_by('appointment_datetime')[:5]
    review_count = SubmitReview.objects.filter(patient=request.user).count()

    total_appointments = appointments.count()

    context = {
        'patient': patient,
        'total_appointments': total_appointments,
        'new_messages': new_messages,
        'review_count': review_count,
        'unread_messages_count': new_messages,
        'upcoming_appointments': upcoming_appointments,
        'appointments': appointments,
        'doctors': doctors,

    }
    return render(request, 'patient_dashboard.html', context)

@login_required
def doctor_dashboard_view(request): 
    
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return HttpResponse("Doctor profile not found.", status=404)

    clinic = doctor.owned_clinics.all()

    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
    else:
        form = DoctorProfileForm(instance=doctor)

    # ✅ MAIN QUERYSET (ONLY THIS DOCTOR)
    appointments_qs = Appointment.objects.filter(
        doctor=doctor,
        payment_status="paid"
    ).select_related('patient')

    # Order
    appointments = appointments_qs.order_by('-appointment_datetime')

    # ✅ PATIENT COUNT (ONLY THIS DOCTOR)
    total_patients = appointments_qs.values_list(
        'patient_id', flat=True
    ).distinct().count()

    # ✅ APPOINTMENT COUNT (ONLY THIS DOCTOR)
    appointment_count = appointments_qs.count()

    # (Optional: if staff should be doctor-specific, adjust this)
    total_staffs = User.objects.filter(
        is_staff=True,
        is_doctor=False
    ).count()

    # Pagination
    paginator = Paginator(appointments, 5)
    page_number = request.GET.get('page')
    appointments = paginator.get_page(page_number)

    context = {
        'doctor': doctor,
        'form': form,
        'appointments': appointments,
        'Total_patient': total_patients,
        'total_staffs': total_staffs,
        'appointment_count': appointment_count,
        'clinic': clinic
    }

    return render(request, 'doctor_dashboard.html', context)

def appointment_detail_view(request, appointment_id):
    try:
        appointment = Appointment.objects.select_related('patient', 'doctor').get(id=appointment_id)
        return JsonResponse({
            'patient': appointment.patient.get_full_name(),
            'datetime': appointment.appointment_datetime.strftime('%Y-%m-%d %H:%M'),
            'purpose' : appointment.purpose,
            'status': appointment.status,
            'appointment_mode': appointment.appointment_mode,
        })
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found.'}, status=404)

@login_required
def doctor_appointment_list(request):
    doctor = get_object_or_404(Doctor, user=request.user)
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            form.save()
    else:
        form = DoctorProfileForm(instance=doctor)


    all_appointments = Appointment.objects.filter(
    doctor=doctor,
    payment_status="paid"
    ).order_by('-appointment_datetime')

    upcoming_appointments_qs = all_appointments.filter(
        appointment_datetime__gte=now()
    ).order_by('appointment_datetime')

    past_appointments_qs = all_appointments.filter(
        appointment_datetime__lt=now()
    ).order_by('-appointment_datetime')
    upcoming_page_number = request.GET.get('upcoming_page', 1)
    upcoming_paginator = Paginator(upcoming_appointments_qs, 5)
    upcoming_appointments = upcoming_paginator.get_page(upcoming_page_number)

    past_page_number = request.GET.get('past_page', 1)
    past_paginator = Paginator(past_appointments_qs, 5)
    past_appointments = past_paginator.get_page(past_page_number)

    context = {
        'form': form,
        'appointments': all_appointments,
        'upcoming_appointments': upcoming_appointments,
        'past_appointments': past_appointments,
        'unread_messages': 0,
        'doctor': doctor,
       
    }
    return render(request, 'appointment.html', context)


def add_appointment(request):
    if request.method == 'POST':
        doctor = Doctor.objects.get(user=request.user)

        patient_name = request.POST.get('patient_name')
        email = request.POST.get('email').strip().lower()
        phone = request.POST.get('phone')
        location = request.POST.get('location')  
        reason = request.POST.get('reason')
        appointment_date = request.POST.get('appointment_datetime')

        if not appointment_date:
            messages.error(request, "Please select a valid appointment date.")
            return redirect('add_appointment')

        try:
            appointment_datetime = datetime.strptime(appointment_date, '%Y-%m-%dT%H:%M')
            appointment_datetime = make_aware(appointment_datetime)
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('add_appointment')

        appointment_end = appointment_datetime + timedelta(minutes=30)

        schedule = ScheduleTiming.objects.filter(
            doctor=doctor,
            start_datetime=appointment_datetime
        ).first()

        if not schedule:
            schedule = ScheduleTiming.objects.create(
                doctor=doctor,
                date=appointment_datetime.date(),
                start_datetime=appointment_datetime,
                end_datetime=appointment_end,
                is_available=False,
                title="Booked slot",
                description="Auto-created from appointment",
            )  
        user_obj, user_created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': patient_name.split()[0] if patient_name else '',
                'last_name': ' '.join(patient_name.split()[1:]) if patient_name and len(patient_name.split()) > 1 else '',
                'is_patient': True
            }
        )

        if not user_created:
            if not user_obj.first_name and patient_name:
                user_obj.first_name = patient_name.split()[0]
            if not user_obj.last_name and patient_name:
                user_obj.last_name = ' '.join(patient_name.split()[1:])
            user_obj.save()

        
        patient, patient_created = Patient.objects.get_or_create(
            user=user_obj,
            defaults={
                'email': email,
                'mobile_number': phone,
                'first_name': user_obj.first_name,
                'last_name': user_obj.last_name,
            }
        )

        if not patient_created and patient.mobile_number != phone:
            patient.mobile_number = phone
            patient.save()


        time_slot = TimeSlot.objects.first() 

        Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            time_slot=time_slot,
            appointment_datetime=appointment_datetime,
            location=location,
            purpose=reason,
            patient_name=patient_name,
            patient_email=email,
            patient_mobile_number=phone,
            status='Pending',
            payment_status='pending',
            schedule=schedule
        )

        messages.success(request, "Appointment successfully added.")
        return redirect('doctor_appointment_list')

    return render(request, 'appointment.html')

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Appointment


@login_required
def complete_appointment(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":

        prescription_text = request.POST.get("prescription")

        prescription_file = request.FILES.get("prescription_file")

        appointment.prescription = prescription_text

        if prescription_file:
            appointment.prescription_file = prescription_file

        appointment.status = "Completed"

        appointment.save()

        messages.success(request, "Appointment completed and prescription saved.")

    return redirect('doctor_appointment_list')

@login_required
def accept_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor_profile)

    appointment.status = 'Accepted'
    appointment.save()

    subject = 'Your Appointment is Confirmed'

    message = f"""
Dear {appointment.patient.get_full_name()},

Your appointment with Dr. {appointment.doctor.user.get_full_name()} has been accepted.

Appointment Details:
Date & Time: {appointment.appointment_datetime.strftime('%Y-%m-%d %H:%M')}
Location: {appointment.location}
Reason: {appointment.purpose}
Appointment Mode: {appointment.appointment_mode.capitalize()}
"""
    if appointment.appointment_mode == 'online' and appointment.zoom_link:
        message += f"\nZoom Link: {appointment.zoom_link}\nPlease join the meeting on time."

    message += """
Please arrive at least 10 minutes early (or join online 5 minutes before start).

Thank you,
Doctor Appointment Booking Team
"""


    recipient_email = appointment.patient_email or getattr(appointment.patient, 'email', None)

    if recipient_email:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        messages.success(request, "Appointment accepted and confirmation email sent to the patient.")
    else:
        messages.warning(request, "Appointment accepted, but email not sent (email address missing).")

    return redirect('doctor_appointment_list')

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor_profile)
    appointment.status = 'Cancelled'
    appointment.save()

    
    subject = 'Appointment Cancelled'
    message = f"""
    Dear {appointment.patient.get_full_name()},

    We regret to inform you that your appointment scheduled on
    {appointment.appointment_datetime.strftime('%Y-%m-%d %H:%M')} with Dr. {appointment.doctor.user.get_full_name()}
    has been cancelled.

    If you have any questions, feel free to contact the clinic.

    Thank you,
    Doctor Appointment System
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [appointment.patient.user.email], 
        fail_silently=False,
    )

    return redirect('doctor_appointment_list')

@login_required
def edit_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        appointment.patient_name = request.POST.get('patient_name')
        appointment.patient_email = request.POST.get('email')
        appointment.patient_mobile_number = request.POST.get('phone')
        appointment.purpose = request.POST.get('purpose')
        appointment.location = request.POST.get('location')
        appointment_mode = request.POST.get('appointment_mode')
        appointment.appointment_mode = appointment_mode

 
        zoom_link_input = request.POST.get('zoom_link')
        if appointment_mode == 'online':
            appointment.zoom_link = zoom_link_input.strip() if zoom_link_input else ''
        else:
            appointment.zoom_link = ''  

        if appointment.patient:
            appointment.patient.location = appointment.location
            appointment.patient.save()

        dt_str = request.POST.get('appointment_datetime')
        try:
            appointment.appointment_datetime = make_aware(datetime.strptime(dt_str, '%Y-%m-%dT%H:%M'))
        except ValueError:
            messages.error(request, "Invalid appointment date and time format.")
            return redirect('edit_appointment', appointment_id=appointment.id)

        appointment.save()
        messages.success(request, "Appointment updated successfully.")
        return redirect('doctor_appointment_list')

    return render(request, 'edit_appointment.html', {
        'appointment': appointment,
    })


def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.delete()
    return redirect('doctor_appointment_list')

from django.forms import  inlineformset_factory, modelformset_factory

@login_required
def my_profile(request):
    """Doctor profile management view"""

    ClinicFormSet = modelformset_factory(Clinic, form=ClinicForm, extra=1, can_delete=True)

    EducationFormSet = inlineformset_factory(
        Doctor, Education, form=EducationForm, extra=1, can_delete=True
    )

    ExperienceFormSet = inlineformset_factory(
        Doctor, Experience, form=ExperienceForm, extra=1, can_delete=True
    )

    AwardFormSet = inlineformset_factory(
        Doctor, Award, form=AwardForm, extra=1, can_delete=True
    )

    SpecialityFormSet = inlineformset_factory(
        Doctor, Speciality, form=SpecialityForm, extra=1, can_delete=True
    )

    if not hasattr(request.user, 'doctor_profile'):
        messages.error(request, "Access denied. Doctor account required.")
        return redirect('login')

    doctor_profile, _ = Doctor.objects.get_or_create(user=request.user)

    if request.method == 'POST':

        profile_form = DoctorProfileForm(
            request.POST,
            request.FILES,
            instance=doctor_profile,
            user=request.user
        )

        clinic_formset = ClinicFormSet(request.POST, request.FILES, queryset=Clinic.objects.none())

        education_formset = EducationFormSet(request.POST, instance=doctor_profile)
        experience_formset = ExperienceFormSet(request.POST, instance=doctor_profile)
        award_formset = AwardFormSet(request.POST, instance=doctor_profile)
        speciality_formset = SpecialityFormSet(request.POST, instance=doctor_profile)

        if (
            profile_form.is_valid()
            and clinic_formset.is_valid()
            and education_formset.is_valid()
            and experience_formset.is_valid()
            and award_formset.is_valid()
            and speciality_formset.is_valid()
        ):

            try:
                with transaction.atomic():

                    doctor_profile = profile_form.save()

                    education_formset.instance = doctor_profile
                    experience_formset.instance = doctor_profile
                    award_formset.instance = doctor_profile
                    speciality_formset.instance = doctor_profile

                    education_formset.save()
                    experience_formset.save()
                    award_formset.save()
                    speciality_formset.save()

    
                    for form in clinic_formset:

                        if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                            continue

                        name = form.cleaned_data.get("name")
                        city = form.cleaned_data.get("city")
                        address = form.cleaned_data.get("address")

                        if not name:
                            continue

                        clinic_name = name.strip().upper()

                        clinic = Clinic.objects.filter(name__iexact=clinic_name).first()

                        if clinic:
                
                            doctor_profile.clinics.add(clinic)

                            messages.info(
                                request,
                                f"Doctor linked to existing clinic '{clinic.name}'."
                            )

                        else:
                
                            clinic = Clinic.objects.create(
                                name=clinic_name,
                                city=city,
                                address=address,
                                doctor=doctor_profile
                            )

                            doctor_profile.clinics.add(clinic)

                            messages.success(
                                request,
                                f"New clinic '{clinic.name}' created and linked."
                            )

                messages.success(request, "Profile updated successfully!")
                return redirect("my_profile")

            except Exception as e:
                messages.error(request, f"Error occurred: {str(e)}")

        else:
            messages.error(request, "Please correct the errors in the form.")

    else:

        profile_form = DoctorProfileForm(
            instance=doctor_profile,
            user=request.user
        )

        clinic_formset = ClinicFormSet(queryset=doctor_profile.clinics.all())

        education_formset = EducationFormSet(instance=doctor_profile)
        experience_formset = ExperienceFormSet(instance=doctor_profile)
        award_formset = AwardFormSet(instance=doctor_profile)
        speciality_formset = SpecialityFormSet(instance=doctor_profile)

    context = {
        "doctor": doctor_profile,
        "profile_form": profile_form,
        "clinic_formset": clinic_formset,
        "education_formset": education_formset,
        "experience_formset": experience_formset,
        "award_formset": award_formset,
        "speciality_formset": speciality_formset,
        "form": profile_form,
    }

    return render(request, "my-profile.html", context)

def group_time_slots(slots): 
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_to_index = {day: i for i, day in enumerate(days_order)}

    slot_list = []
    for slot in slots:
        for day in slot.day_of_week.split(','):
            slot_list.append((
                day.strip(),
                slot.start_time.strftime("%I:%M %p"),
                slot.end_time.strftime("%I:%M %p"),
                slot.is_available
            ))
    slot_list.sort(key=lambda x: day_to_index[x[0]])    
    grouped = []
    i = 0
    while i < len(slot_list):
        day_range = [slot_list[i][0]]
        start_time, end_time, available = slot_list[i][1], slot_list[i][2], slot_list[i][3]

        while (i + 1 < len(slot_list) and
               slot_list[i + 1][1] == start_time and
               slot_list[i + 1][2] == end_time and
               slot_list[i + 1][3] == available and
               day_to_index[slot_list[i + 1][0]] == day_to_index[slot_list[i][0]] + 1):
            i += 1
            day_range.append(slot_list[i][0])
        if len(day_range) == 1:
            day_str = day_range[0]
        else:
            day_str = f"{day_range[0]} to {day_range[-1]}"

        grouped.append({
            'day_range': day_str,
            'time_range': f"{start_time} - {end_time}",
            'available': available
        })
        i += 1

    return grouped

@login_required
def update_appointment_status(request, appointment_id):

    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":
        new_status = request.POST.get("status")

        if new_status in ["Pending", "Accepted", "Cancelled"]:
            appointment.status = new_status
            appointment.save()

    return redirect(request.META.get("HTTP_REFERER"))


@login_required
def schedule_timing_view(request):

    doctor_user = request.user

    try:
        doctor = Doctor.objects.get(user=doctor_user)

    except Doctor.DoesNotExist:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_profile_setup')


    time_slots = TimeSlot.objects.filter(doctor=doctor)


    DAY_ORDER = [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday'
    ]


    def compress_days(days_list):
        ordered = [day for day in DAY_ORDER if day in days_list]

        if len(ordered) == 1:
            return ordered[0]

        if len(ordered) > 1:
            return f"{ordered[0]} - {ordered[-1]}"

        return ""


    grouped_slots = group_time_slots(time_slots)


    time_slot_data = []

    for slot in time_slots:

        days_list = slot.get_days_list()

        time_slot_data.append({
            'id': slot.id,
            'days': compress_days(days_list),
            'day_of_week': slot.day_of_week,
            'start_time': slot.start_time.strftime('%H:%M'),
            'end_time': slot.end_time.strftime('%H:%M'),
            'available': slot.is_available,
        })


    days = [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday'
    ]


    return render(request, 'schedule-timing.html', {
        'grouped_slots': grouped_slots,
        'time_slots': time_slot_data,
        'days': days,
        'doctor': doctor,
    })

@login_required
def calendar_events(request):
    events = []
    try:
        doctor = Doctor.objects.get(user=request.user)
        appointments = Appointment.objects.filter(
            doctor=doctor,
            status__in=["Accepted", "Pending", "Cancelled"],
            appointment_datetime__gte=date.today()
        )

        for appt in appointments:
            patient_name = (
                appt.patient.user.get_full_name()
                if appt.patient and appt.patient.user
                else appt.patient_name or "Unknown"
            )
            purpose = appt.purpose or "Checkup"
            appointment_mode = appt.appointment_mode.capitalize()

            status_color = {
                "Accepted": "green",
                "Cancelled": "red",
                "Pending": "orange"
            }.get(appt.status, "gray")
            description = f"Mode: {appointment_mode}\nPurpose: {purpose}"
            if appt.appointment_mode == "online" and appt.zoom_link:
                description += f"\nZoom Link: {appt.zoom_link}"

            events.append({
                "title": f"{patient_name} - {purpose} , {appointment_mode},{appt.zoom_link}",
                "start": appt.appointment_datetime.isoformat(),
                "end": appt.appointment_datetime.isoformat(),
                "color": status_color,
                "description": description,  
                "url": appt.zoom_link if appt.appointment_mode == "online" and appt.zoom_link else "", 
            })

    except Doctor.DoesNotExist:
        pass

    return JsonResponse(events, safe=False)

@login_required
def add_or_edit_time_slot(request):

    doctor=get_object_or_404(Doctor,user=request.user)

    if request.method=="POST":

        slot_id=request.POST.get("slot_id")

        days=request.POST.getlist("day_of_week")

        start_time=parse_time(request.POST.get("start_time"))
        end_time=parse_time(request.POST.get("end_time"))

        is_available="is_available" in request.POST


        if slot_id:

            slot=get_object_or_404(TimeSlot,id=slot_id,doctor=doctor)

            slot.day_of_week=",".join(days)

            slot.start_time=start_time
            slot.end_time=end_time

            slot.is_available=is_available

            slot.save()

        else:

            for day in days:

                TimeSlot.objects.create(
                    doctor=doctor,
                    day_of_week=day,
                    start_time=start_time,
                    end_time=end_time,
                    is_available=is_available
                )

        return redirect("schedule_timing")

@login_required
def delete_time_slot(request,slot_id):

    slot=get_object_or_404(TimeSlot,id=slot_id,doctor__user=request.user)

    slot.delete()

    return redirect("schedule_timing")


@login_required
def my_patients(request): 
   
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return HttpResponse("Doctor profile not found.", status=404)

    
    patients_list = Patient.objects.filter(
        Q(doctor=request.user) | Q(appointments__doctor=doctor)
    ).distinct()

    search_query = request.GET.get('search', '').strip()
    full_name = Concat('first_name', V(' '), 'last_name')

    if search_query:
        patients_list = patients_list.annotate(full_name=full_name).filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(full_name__icontains=search_query)
        )

    paginator = Paginator(patients_list, 10)  
    page_number = request.GET.get('page')
    patients = paginator.get_page(page_number)

    return render(request, 'my-patients.html', {
        'doctor': doctor,
        'patients': patients,
        'search_query': search_query,
        
    })

@login_required
def add_patient(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return HttpResponse("Doctor profile not found.", status=404)

    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.doctor = request.user  
            patient.save()
            messages.success(request, "Patient added successfully.")
            return redirect('my_patients')
        else:
            messages.error(request, "There was a problem with the form.")
    else:
        form = PatientForm()
    return render(request, 'patient_form.html', {
        'doctor': doctor,
        'form': form, 
        'action': 'Add'})


@login_required
def edit_patient(request, patient_id):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return HttpResponse("Doctor profile not found.", status=404)

   
    patient = Patient.objects.filter(
    Q(id=patient_id) & (Q(doctor=request.user) | Q(appointments__doctor=doctor))
    ).distinct().first()

    if not patient:
        return HttpResponse("Patient not found.", status=404)
    
    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Patient updated successfully.")
            return redirect('my_patients')
        else:
            messages.error(request, "There was a problem updating the patient.")
    else:
        form = PatientForm(instance=patient)

    return render(request, 'patient_form.html', {
            'doctor': doctor,
            'patient': patient,
            'form': form,
            'action': 'Edit'
            })

@login_required
def delete_patient(request, patient_id):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return HttpResponse("Doctor profile not found.", status=404)
    try:
        patient = Patient.objects.get(
            Q(id=patient_id) & (Q(doctor=request.user) | Q(appointments__doctor=doctor))
        )
    except Patient.DoesNotExist:
        return HttpResponse("You don't have permission to delete this patient.", status=403)

    patient.delete()
    messages.success(request, "Patient deleted successfully.")
    return redirect('my_patients')

@login_required
def add_listing(request):
    
    doctor = request.user.doctor_profile

    if request.method == 'POST':
        
        DoctorListing.objects.filter(doctor=doctor).delete()
        Service.objects.filter(doctor=doctor).delete()  

        treatments = request.POST.getlist('treatment[]')
        prices = request.POST.getlist('price[]')

        for treatment, price in zip(treatments, prices):
            if treatment and price:
                
                DoctorListing.objects.create(
                    doctor=doctor,
                    treatment=treatment,
                    price=price
                )

                Service.objects.create(
                    doctor=doctor,
                    name=treatment,
                    price=price,
                )

        return redirect('add_listing')

    else:
        pricing = DoctorListing.objects.filter(doctor=doctor)
        return render(request, 'add-listing.html', {
            'pricing': pricing,
            'doctor': doctor, 
            
        })

@login_required
def change_password(request):
    doctor = Doctor.objects.get(user=request.user)

    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
 
        if not request.user.check_password(old_password):
            messages.error(request, 'Old password is incorrect.')
        elif not new_password1 or not new_password2:
            messages.error(request, 'New password fields cannot be empty.')
        elif new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        else:
           
            request.user.set_password(new_password1)
            request.user.save()

            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Password changed successfully.')
            return redirect('doctor_dashboard')

    context = {
    'doctor': doctor
}
    return render(request, 'change_password.html',context)

@login_required
def profile(request):
    
    try:
        patient_profile, _ = Patient.objects.get_or_create(user=request.user)
        social_links, _ = PatientSocialLinks.objects.get_or_create(patient=patient_profile)

        if request.method == 'POST':
            form = PatientForm(request.POST, request.FILES, instance=patient_profile)
            social_form = SocialLinksForm(request.POST, instance=social_links)

            if form.is_valid() and social_form.is_valid():
                try:
                    with transaction.atomic():
                       
                        request.user.first_name = form.cleaned_data['first_name']
                        request.user.last_name = form.cleaned_data['last_name']
                        request.user.email = form.cleaned_data['email']
                        request.user.save()

                        form.save()

                        social_form.save()

                        messages.success(request, 'Profile updated successfully!')
                        return redirect(reverse('profile') + '?success=true')

                except Exception as e:
                    messages.error(request, f'Error updating profile: {e}')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
                for field, errors in social_form.errors.items():
                    for error in errors:
                        messages.error(request, f'Social {field}: {error}')
        else:
            form = PatientForm(instance=patient_profile)
            social_form = SocialLinksForm(instance=social_links)

       
        unread_messages_count = Message.objects.filter(receiver=request.user, is_read=False).count()

        return render(request, 'patient_profile.html', {
            'form': form,
            'social_form': social_form,
            'patient': patient_profile,
            'unread_messages_count': unread_messages_count,
            'user': request.user,
            
        })
    except Exception as e:
        raise e
    

@login_required
def change_password2(request):
    
    patient_profile, created = Patient.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        old = request.POST.get('old_password')
        new1 = request.POST.get('new_password1')
        new2 = request.POST.get('new_password2')

        if not request.user.check_password(old):
            messages.error(request, 'Old password is incorrect.')
        elif new1 != new2:
            messages.error(request, 'New passwords do not match.')
        else:
            request.user.set_password(new1)
            request.user.save()
            update_session_auth_hash(request, request.user)  
            messages.success(request, 'Password changed successfully.')
            return redirect('patient_dashboard')

    context = {
        'patient': patient_profile,
        
    }
    return render(request, 'change_password2.html', context)



from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import razorpay

@login_required(login_url='login')
def book_appointment(request, id, slug=None):
    doctor = get_object_or_404(Doctor, id=id)

    if slug and slug != doctor.slug:
        return redirect('book_appointment', id=doctor.id, slug=doctor.slug)

    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.error(request, "You must be logged in as a patient to book an appointment.")
        return redirect('login')

    if request.method == 'POST':

        selected_date = request.POST.get('date')
        selected_time = request.POST.get('time')

        if not selected_date or not selected_time:
            return HttpResponse("Missing date or time", status=400)

        appointment_datetime = timezone.make_aware(
            timezone.datetime.strptime(f"{selected_date} {selected_time}", "%Y-%m-%d %H:%M")
        )

        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_datetime=appointment_datetime,
            date=selected_date,
            time=selected_time,

        
            is_new_patient=(request.POST.get('is_new_patient') == 'yes'),
            gender=request.POST.get('gender'),
            patient_name=request.POST.get('patient_name'),
            patient_email=request.POST.get('patient_email'),
            patient_mobile_number=request.POST.get('patient_mobile_number'),
            purpose=request.POST.get('purpose'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            zip_code=request.POST.get('zip_code'),
            date_of_birth=request.POST.get('date_of_birth'),
            appointment_notes=request.POST.get('appointment_notes'),

    
            appointment_type=request.POST.get('appointment_type', 'consultation'),
            status='Pending',

            fee=request.POST.get('fee', 0),
            total_amount=request.POST.get('total_amount', 0),
            payment_status=request.POST.get('payment_status', 'pending'),

            appointment_mode=request.POST.get("appointment_mode", "offline"),
        )

        return redirect('confirm_appointment', appointment.id)

    selected_date = request.POST.get('date') or request.GET.get('date')
    selected_time = request.POST.get('time') or request.GET.get('time')

    selected_services_ids = request.GET.getlist('services')
    services = Service.objects.filter(id__in=selected_services_ids)

    total_amount = sum(service.price for service in services)

    return render(request, 'book_appointment.html', {
        'doctor': doctor,
        'patient': patient,
        'selected_date': selected_date,
        'selected_time': selected_time,
        'selected_services_info': services,
        'total_amount': total_amount,
        'doctor_profile': getattr(request.user, 'doctor_profile', None),
        'patient_profile': getattr(request.user, 'patient_profile', None),
    })

@login_required
def confirm_appointment(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient__user=request.user
    )

    return render(
        request,
        "confirmation_razorpay.html",
        {
            "appointment": appointment,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        }
    )


@login_required
def create_razorpay_order(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient__user=request.user
    )

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    order = client.order.create({
        "amount": int(appointment.total_amount * 100),
        "currency": "INR",
        "payment_capture": 1
    })

    appointment.razorpay_order_id = order["id"]
    appointment.save()

    return JsonResponse({
        "order_id": order["id"],
        "key": settings.RAZORPAY_KEY_ID,
        "amount": appointment.total_amount,
        "name": "Doctor Appointment",
        "email": appointment.patient_email,
        "contact": appointment.patient_mobile_number,
    })



@csrf_exempt
def payment_success(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request")

    appointment = None

    try:
        data = json.loads(request.body)

        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_signature = data.get("razorpay_signature")

        if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
            return JsonResponse({"status": "failed", "error": "Missing Razorpay data"})

        appointment = Appointment.objects.get(razorpay_order_id=razorpay_order_id)

        if appointment.payment_status == "paid":
            return JsonResponse({"status": "success"})
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })

        appointment.payment_status = "paid"
        appointment.status = "Accepted"
        appointment.razorpay_payment_id = razorpay_payment_id
        appointment.razorpay_signature = razorpay_signature

        
        video_text = ""
        if appointment.appointment_mode == "online":
            appointment.video_link = f"https://meet.jit.si/appointment-{appointment.id}"
            appointment.zoom_link = appointment.video_link
            video_text = f"\n\nVideo Call Link:\n{appointment.video_link}"

        appointment.save()

        appointment_time = appointment.appointment_datetime.strftime("%Y-%m-%d %H:%M")

        send_mail(
            subject="Appointment Confirmed ✅",
            message=(
                f"Dear {appointment.patient_name},\n\n"
                f"Your appointment has been successfully confirmed.\n\n"
                f"Doctor: Dr. {appointment.doctor.user.get_full_name()}\n"
                f"Date & Time: {appointment_time}\n"
                f"Mode: {appointment.appointment_mode.capitalize()}"
                f"{video_text}\n\n"
                f"Thank you for choosing our service."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.patient_email],
            fail_silently=True,
        )

        send_mail(
            subject="New Appointment Booked 📅",
            message=(
                f"Dear Dr. {appointment.doctor.user.first_name},\n\n"
                f"A new appointment has been booked.\n\n"
                f"Patient Name: {appointment.patient_name}\n"
                f"Date & Time: {appointment_time}\n"
                f"Mode: {appointment.appointment_mode.capitalize()}"
                f"{video_text}\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appointment.doctor.user.email],
            fail_silently=True,
        )

        return JsonResponse({"status": "success"})

    except Appointment.DoesNotExist:
        return JsonResponse({"status": "failed", "error": "Appointment not found"})

    except Exception as e:
        if appointment:
            appointment.payment_status = "failed"
            appointment.save()

            send_mail(
                subject="Payment Failed ❌",
                message=(
                    f"Dear {appointment.patient_name},\n\n"
                    f"Unfortunately, your payment could not be completed.\n\n"
                    f"Please retry your booking or payment.\n"
                    f"If the amount was deducted, it will be refunded automatically.\n\n"
                    f"Thank you."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.patient_email],
                fail_silently=True,
            )

        return JsonResponse({"status": "failed", "error": str(e)})



@login_required
def manage_time_slots(request):
    doctor = request.user.doctor  
    if request.method == 'POST':
        form = TimeSlotForm(request.POST)
        if form.is_valid():
            timeslot = form.save(commit=False)
            timeslot.doctor = doctor
            timeslot.save()
            return redirect('manage_time_slots')  
    else:
        form = TimeSlotForm()

    time_slots = TimeSlot.objects.filter(doctor=doctor)

    context = {
        'form': form,
        'time_slots': time_slots,
    }
    return render(request, 'schedule-timing.html', context)

def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm', args=[uid, token])
            )

            message = render_to_string('password_reset_email.html', {
                'user': user,
                'reset_url': reset_url
            })

            send_mail(
                'Reset Your Password',
                message,
                'no-reply@docpro.com',
                [email],
                fail_silently=False
            )

        except User.DoesNotExist:
            pass  # 🔥 Do nothing (security)

        messages.success(request, 'If an account exists, a reset link has been sent.')
        return redirect('login')
    return redirect('login')


def password_reset_confirm(request, uidb64, token):
    try:
        uid = int(urlsafe_base64_decode(uidb64).decode())
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return redirect(request.path)

            user.set_password(new_password)
            user.save()
            messages.success(request, 'Your password has been reset. You can now log in.')
            return redirect('login')

        return render(request, 'password_reset_confirm.html', {
            'validlink': True,
            'uid': uidb64,
            'token': token
        })
 
    messages.error(request, 'Reset link is invalid or expired.')
    return render(request, 'password_reset_confirm.html', {
        'validlink': False
    })
def doctor_list_view(request, slug=None): 
    query = request.GET.get('q', '')
    specialization = request.GET.get('specialization', '')

    doctors = Doctor.objects.filter(user__is_active=True)               

    # 🔥 NEW (slug support)
    if slug:
        parts = slug.split('-')
        city = parts[-1]
        specialization_from_slug = " ".join(parts[:-1])

        doctors = doctors.filter(
            specialization__icontains=specialization_from_slug,
            city__icontains=city
        )

        specialization = specialization_from_slug

    # EXISTING (unchanged)
    if query:
        doctors = doctors.filter(
            Q(user__first_name__icontains=query) |
            Q(city__icontains=query)
        )

    if specialization:
        doctors = doctors.filter(specialization__iexact=specialization)

    specializations = Doctor.objects.values_list('specialization', flat=True).distinct()
    paginator = Paginator(doctors.order_by('-is_featured', '-average_rating'), 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    doctor = getattr(request.user, 'doctor_profile', None)
    patient = getattr(request.user, 'patient_profile', None)

    context = {
        'page_obj': page_obj,
        'query': query,
        'specializations': specializations,
        'selected_specialization': specialization,
        'doctor': doctor,
        'patient': patient,
    }

    return render(request, 'doctor_list.html', context)

def calculate_experience_years(from_date, to_date):
    if not to_date:
        to_date = date.today()
    delta = relativedelta(to_date, from_date)
    return f"{delta.years} years and {delta.months} months"

from collections import defaultdict

DAY_ORDER = [
    "Monday","Tuesday","Wednesday",
    "Thursday","Friday","Saturday","Sunday"
]


def group_schedule(time_slots):

    schedule = defaultdict(list)

    for slot in time_slots:
        key = (slot.start_time, slot.end_time)
        schedule[key].append(slot.day_of_week)

    grouped = []

    for (start, end), days in schedule.items():

        days = sorted(days, key=lambda d: DAY_ORDER.index(d))

        day_ranges = []
        start_day = days[0]
        prev_index = DAY_ORDER.index(days[0])

        for day in days[1:]:

            current_index = DAY_ORDER.index(day)

            if current_index == prev_index + 1:
                prev_index = current_index
            else:
                day_ranges.append((start_day, DAY_ORDER[prev_index]))
                start_day = day
                prev_index = current_index

        day_ranges.append((start_day, DAY_ORDER[prev_index]))

        grouped.append({
            "day_ranges": day_ranges,
            "start_time": start,
            "end_time": end
        })

    return grouped

from django.shortcuts import get_object_or_404, redirect
from django.db.models import Avg

def doctor_detail_view(request, slug):
    doctor = get_object_or_404(Doctor, slug=slug)
    # ✅ SEO FIX: Redirect if slug is wrong
    if doctor.slug != slug:
        return redirect('doctor_detail', slug=doctor.slug)

    services = Service.objects.filter(doctor=doctor)
    experiences = doctor.experience_set.all()
    reviews = SubmitReview.objects.filter(doctor=doctor).order_by('-created_at')

    time_slots = TimeSlot.objects.filter(
        doctor=doctor,
        is_available=True
    ).order_by('day_of_week', 'start_time')

    grouped_slots = group_schedule(time_slots)

    # EXPERIENCE DATA
    experience_data = []
    for exp in experiences:
        duration = calculate_experience_years(exp.from_date, exp.to_date)
        experience_data.append({
            'hospital_name': exp.hospital_name,
            'designation': exp.designation,
            'from_date': exp.from_date,
            'to_date': exp.to_date,
            'duration': duration
        })

    patient = None
    doctor_profile = None

    if request.user.is_authenticated:
        try:
            patient = request.user.patient_profile
        except:
            patient = None
        try:
            doctor_profile = request.user.doctor_profile
        except:
            doctor_profile = None

    # APPOINTMENT BOOKING
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            if not patient:
                messages.error(request, "You must be logged in as a patient to book an appointment.")
                return redirect('login')

            appointment = form.save(commit=False)
            appointment.doctor = doctor
            appointment.patient = patient
            appointment.save()
            form.save_m2m()

            messages.success(request, "Appointment booked successfully!")
            return redirect('appointment_success')
    else:
        form = AppointmentForm()

    # REVIEWS
    total_reviews = reviews.count()
    average_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0

    return render(request, 'doctor_detail.html', {
        'doctor': doctor,
        'services': services,
        'form': form,
        'experience_data': experience_data,
        'grouped_slots': grouped_slots,
        'patient': patient,
        'doctor_profile': doctor_profile,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'average_rating': round(average_rating, 2),
    })


def get_available_slots(request, doctor_id):

    doctor = get_object_or_404(Doctor, id=doctor_id)

    selected_date = request.GET.get("date")

    if not selected_date:
        return JsonResponse({"slots": []})

    date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    weekday = date_obj.strftime("%A")

    # ✅ Fetch all slots
    slots = TimeSlot.objects.filter(
        doctor=doctor,
        day_of_week=weekday,
        is_available=True
    )

    # 🔥 FETCH ALL BOOKED TIMES ONCE (KEY FIX)
    booked_times = set(
        Appointment.objects.filter(
            doctor=doctor,
            appointment_datetime__date=date_obj.date(),
            status__in=["Pending", "Accepted"]
        ).values_list("appointment_datetime__time", flat=True)
    )

    available_slots = []

    for slot in slots:

        start = datetime.combine(date_obj.date(), slot.start_time)
        end = datetime.combine(date_obj.date(), slot.end_time)

        current = start

        while current < end:

            next_time = current + timedelta(minutes=15)

            if next_time > end:
                break

            # ✅ CHECK IN MEMORY (NO DB HIT)
            if current.time() not in booked_times:
                available_slots.append(current.strftime("%H:%M"))

            current = next_time

    return JsonResponse({"slots": available_slots})

def doctor_reviews(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    sort_option = request.GET.get('sort', 'any')

    if sort_option == 'latest':
        reviews_qs = SubmitReview.objects.filter(doctor=doctor).order_by('-created_at')
    elif sort_option == 'oldest':
        reviews_qs = SubmitReview.objects.filter(doctor=doctor).order_by('created_at')
    else:
        reviews_qs = SubmitReview.objects.filter(doctor=doctor).order_by('-created_at')

    if request.method == 'POST' and request.user == doctor.user:
        review_id = request.POST.get('review_id')
        reply = request.POST.get('reply')
        if review_id and reply:
            review = SubmitReview.objects.get(id=review_id)
            review.reply = reply
            review.reply_created_at = timezone.now()
            review.save()
            return redirect('doctor_reviews', doctor_id=doctor_id)

    paginator = Paginator(reviews_qs, 5)
    page_number = request.GET.get('page')
    reviews = paginator.get_page(page_number)

    context = {
        'doctor': doctor,
        'reviews': reviews,
    }
    return render(request, 'review.html', context)

@login_required
def submit_review(request):
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data['rating'] = request.POST.get('rating')

        form = SubmitReviewForm(post_data)
        if form.is_valid():
            review = form.save(commit=False)
            review.patient = request.user
            review.doctor = form.cleaned_data['doctor'] 
            review.save()
            doctor_reviews = SubmitReview.objects.filter(doctor=review.doctor)
            review.doctor.total_reviews = doctor_reviews.count()
            review.doctor.average_rating = round(
                doctor_reviews.aggregate(Avg('rating'))['rating__avg'] or 0, 2
            )
            review.doctor.save()

            messages.success(request, "Thank you! Your review has been submitted.")
            return redirect('submit_review')
        else:
            messages.error(request, "Please fix the errors in your submission.")
    else:
        form = SubmitReviewForm()

    return render(request, 'submit_review.html', {
        'form': form,
        'available_doctors': Doctor.objects.all(),
        'patient': getattr(request.user, 'patient_profile', None),
        'logged_in_doctor': getattr(request.user, 'doctor_profile', None),
    })
def contact_us(request):
    doctor = None
    patient = None
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None

        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None

    return render(request, 'contact.html', {
        'doctor': doctor,
        'patient': patient,
        
    })

 
def about_us(request):
    doctor = None
    patient = None
 
    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)

        except Doctor.DoesNotExist:
            doctor = None

        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None 
            
    return render(request, 'about.html', {
        'doctor': doctor,
        'patient': patient,
        
    })

import re
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Clinic, Doctor, Patient, ClinicService


def clinic(request, id, slug=None):
    clinic = get_object_or_404(Clinic, id=id)

    # SEO redirect (same)
    if slug and slug != clinic.slug:
        return redirect('clinic', id=clinic.id, slug=clinic.slug)

    doctor = None
    patient = None

    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            doctor = None

        if not doctor:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                patient = None

    # ✅ FIX: use existing clinic (no logic change)
    doctors = clinic.assigned_doctors.all()

    if clinic.doctor and clinic.doctor not in doctors:
        doctors = list(doctors) + [clinic.doctor]

    paginator = Paginator(doctors, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    can_edit_clinic = False
    if request.user.is_authenticated and request.user == clinic.admin:
        can_edit_clinic = True

    raw_specs = clinic.specifications or []

    if isinstance(raw_specs, list):
        specifications = raw_specs

    elif isinstance(raw_specs, str):
        raw_specs = re.sub(r'\d+\.', '', raw_specs)

        # ✅ FIX ONLY (same intent)
        specifications = [
            s.strip()
            for s in raw_specs.split(',')   # ← ONLY FIX
            if s.strip()
        ]

    else:
        specifications = []

    half = (len(specifications) + 1) // 2
    specs_left = specifications[:half]
    specs_right = specifications[half:]

    numbered_specs = [
        f"{i+1}.{spec}" for i, spec in enumerate(specifications)
    ]

    awards = []

    if isinstance(clinic.awards, str):
        awards = [a.strip() for a in clinic.awards.split(',') if a.strip()]

    elif isinstance(clinic.awards, list):
        awards = clinic.awards

    services = ClinicService.objects.filter(clinic=clinic)

    gallery_images = clinic.images.all() if hasattr(clinic, 'images') else []

    return render(request, 'clinic.html', {
        "clinic": clinic,
        "form": ClinicForm(instance=clinic),
        "doctor": doctor,
        "patient": patient,
        "page_obj": page_obj,
        "specifications": specifications,
        "specs_left": specs_left,
        "specs_right": specs_right,
        "numbered_specs": numbered_specs,
        "services": services,
        "awards": awards,
        "gallery_images": gallery_images,
        "can_edit_clinic": can_edit_clinic,
    })
@login_required
def edit_clinic(request, clinic_id):

    user = request.user

    try:
        clinic = Clinic.objects.get(id=clinic_id)
    except Clinic.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Clinic not found.'
        }, status=404)

    if clinic.admin != user and not user.is_superuser:
        return JsonResponse({
            'success': False,
            'error': 'Permission denied.'
        }, status=403)

    if request.method == 'POST':

        form = ClinicForm(request.POST, request.FILES, instance=clinic)

        if form.is_valid():
            clinic = form.save()

            data = {
                'name': clinic.name,
                'tagline': clinic.tagline,
                'description': clinic.description,
                'address': clinic.address,
                'phone': clinic.phone,
                'image_url': clinic.image.url if clinic.image else ''
            }

            return JsonResponse({
                'success': True,
                'clinic': data
            })

        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method.'
    }, status=405)

@login_required
def add_branch(request, clinic_id):

    clinic = get_object_or_404(Clinic, id=clinic_id)

    if request.user != clinic.admin and not request.user.is_superuser:
        return JsonResponse(
            {'success': False, 'error': 'Permission denied'},
            status=403
        )

    if request.method == 'POST':

        form = BranchForm(request.POST)

        if form.is_valid():
            branch = form.save(commit=False)
            branch.clinic = clinic
            branch.save()

    return redirect('clinic', clinic_id=clinic.id)

@login_required
def edit_branch(request, branch_id):

    branch = get_object_or_404(Branch, id=branch_id)
    clinic = branch.clinic

    if request.user != clinic.admin and not request.user.is_superuser:
        return JsonResponse(
            {'success': False, 'error': 'Permission denied'},
            status=403
        )

    if request.method == 'POST':

        form = BranchForm(request.POST, instance=branch)

        if form.is_valid():
            form.save()

    return redirect('clinic', clinic_id=clinic.id)

@login_required
def delete_branch(request, branch_id):

    branch = get_object_or_404(Branch, id=branch_id)
    clinic = branch.clinic

    if request.user != clinic.admin and not request.user.is_superuser:
        return JsonResponse(
            {'success': False, 'error': 'Permission denied'},
            status=403
        )

    clinic_id = clinic.id
    branch.delete()

    return redirect('clinic', clinic_id=clinic_id)
@login_required
def edit_clinic_overview(request, clinic_id):

    clinic = get_object_or_404(Clinic, id=clinic_id)
    user = request.user

    allowed = False

    if hasattr(user, 'doctor_profile'):
        doctor = user.doctor_profile

        if clinic.doctor == doctor or doctor in clinic.assigned_doctors.all():
            allowed = True

    if clinic.admin == user or user.is_superuser:
        allowed = True

    if not allowed:
        return JsonResponse(
            {'success': False, 'error': 'Clinic not found or permission denied.'},
            status=403
        )

    if request.method == "POST":

        clinic.about = request.POST.get("about", "").strip()

        raw_specs = request.POST.get("specifications", "")
        import re
        clinic.specifications = [s.strip() for s in re.split(r'\d+\.', raw_specs) if s.strip()]

        raw_awards = request.POST.get("awards", "")
        clinic.awards = [a.strip() for a in raw_awards.split(',') if a.strip()]

        raw_services = request.POST.get("services", "")
        services = []

        for item in raw_services.split('|'):
            parts = item.split('-')
            name = parts[0].strip() if len(parts) > 0 else ''
            price = parts[1].strip() if len(parts) > 1 else '0'

            services.append({
                "name": name,
                "price": price,
                "description": ""
            })

        clinic.services = services

        if request.FILES.getlist('gallery_images'):
            for img in request.FILES.getlist('gallery_images'):
                clinic.images.create(image=img)

        clinic.save()

        return redirect('clinic', clinic_id=clinic.id)

    return redirect('clinic', clinic_id=clinic.id)

@login_required
def delete_gallery_image(request, image_id):
    image = get_object_or_404(GalleryImage, id=image_id)
    user = request.user
    user_clinic = None
    if hasattr(user, 'doctor_profile'):
        doctor = user.doctor_profile
        user_clinic = Clinic.objects.filter(doctor=doctor).first()
        if not user_clinic:
            user_clinic = Clinic.objects.filter(assigned_doctors=doctor).first()
    if not user_clinic and (user.groups.filter(name='clinic_admin').exists() or user.is_superuser):
        user_clinic = Clinic.objects.filter(admin=user).first()
    if not user_clinic or user_clinic != image.clinic:
        return JsonResponse({'success': False, 'error': 'Permission denied or clinic mismatch.'}, status=403)
    image.delete()
    return redirect('clinic', clinic_id=user_clinic.id)

@login_required
def update_clinic_contact(request, clinic_id):

    clinic = get_object_or_404(Clinic, id=clinic_id)

    if request.user != clinic.admin and not request.user.is_superuser:
        return JsonResponse(
            {"success": False, "error": "Permission denied"},
            status=403
        )

    if request.method == "POST":

        clinic.working_hours = request.POST.get('working_hours', '')
        clinic.address = request.POST.get('address', '')
        clinic.phone = request.POST.get('phone', '')
        clinic.fax = request.POST.get('fax', '')
        clinic.email = request.POST.get('email', '')
        clinic.website = request.POST.get('website', '')
        clinic.facebook = request.POST.get('facebook', '')
        clinic.instagram = request.POST.get('instagram', '')
        clinic.twitter = request.POST.get('twitter', '')
        clinic.google_plus = request.POST.get('google_plus', '')

        clinic.save()

        return redirect('clinic', clinic_id=clinic.id)

    return redirect('clinic', clinic_id=clinic.id)

  
from django.db.models import Q
from django.core.exceptions import MultipleObjectsReturned

def clinic_list(request):

    doctor = None
    patient = None

    if request.user.is_authenticated:
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            try:
                patient = Patient.objects.get(user=request.user)
            except Patient.DoesNotExist:
                pass
            except MultipleObjectsReturned:
                patient = Patient.objects.filter(user=request.user).first()
        except MultipleObjectsReturned:
            doctor = Doctor.objects.filter(user=request.user).first()

    category_id = request.GET.get('category_id')
    query = request.GET.get('q', '').strip()

    clinics = Clinic.objects.all()

    # Safe category filter (no crash if invalid)
    if category_id:
        try:
            clinics = clinics.filter(category_id=int(category_id))
        except (ValueError, TypeError):
            pass

    if query:
        clinics = clinics.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query)
        )

    context = {
        'clinics': clinics,
        'doctor': doctor,
        'patient': patient,
        'query': query,
    }

    return render(request, 'clinic_list.html', context)
from django.utils.http import urlencode
from .models import Doctor, Clinic

def search_results(request):
    if request.method == 'POST':
        query = request.POST.get('name', '').strip()
        filter_type = request.POST.get('filter_type', 'all')

        doctors = Doctor.objects.none()
        clinics = Clinic.objects.none()

        doctor_filter = (
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(specialization__icontains=query)
        )

        clinic_filter = (
            Q(name__icontains=query) |
            Q(city__icontains=query)
        )

        if filter_type == 'all':
            doctors = Doctor.objects.filter(doctor_filter).distinct()
            clinics = Clinic.objects.filter(clinic_filter).distinct()
        elif filter_type == 'doctor':
            doctors = Doctor.objects.filter(doctor_filter).distinct()
        elif filter_type == 'clinic':
            clinics = Clinic.objects.filter(clinic_filter).distinct()

        
        if doctors.exists() and not clinics.exists():
            query_string = urlencode({'q': query})
            return redirect(f"{reverse('doctor_list')}?{query_string}")

        elif clinics.exists() and not doctors.exists():
            query_string = urlencode({'q': query})
            return redirect(f"{reverse('Clinic_list')}?{query_string}")

        return render(request, 'base.html', {
            'query': query,
            'doctors': doctors,
            'clinics': clinics,
        })

    return redirect('home')
@login_required
def messages_view(request):
    doctor = request.user.doctor_profile 
    doctor_type = ContentType.objects.get_for_model(doctor)

    messages = Message.objects.filter(
        sender_content_type=doctor_type,
        sender_object_id=doctor.id
    )

    context = {
        'doctor':doctor,
        'messages': messages
    }
    return render(request, 'message.html', context)

@login_required
def favourite_doctors(request):
    patient = get_object_or_404(Patient, user=request.user)
    favourite_list = patient.favourites.all()
    paginator = Paginator(favourite_list, 6) 
    page = request.GET.get('page')
    doctors = paginator.get_page(page)

    return render(request, 'favourite_doctors.html', {
        'doctors': doctors,
        'patient': patient,
        'unread_messages': 0, 
    })

@login_required
def toggle_favourite(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    favourite, created = FavouriteDoctor.objects.get_or_create(user=request.user, doctor=doctor)

    if not created:
        favourite.delete()  

    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def message_dashboard(request):
    
    conversations = Conversation.objects.filter(
        Q(doctor=request.user) | Q(patient=request.user)
    ).order_by('-created_at')

    contacts = []
    for conv in conversations:
        contact = conv.doctor if conv.patient == request.user else conv.patient
        last_message = conv.messages.order_by('-timestamp').first()
        unread_count = conv.messages.filter(is_read=False).exclude(sender=request.user).count()
        contacts.append({
            'user': contact,
            'conversation_id': conv.id,
            'last_message': last_message.content if last_message else '',
            'timestamp': last_message.timestamp if last_message else conv.created_at,
            'unread_count': unread_count,
            'status': 'online' if contact.is_active else 'away',
        })

    selected_conversation_id = request.GET.get('conversation_id')
    selected_conversation = None
    messages = []
    selected_contact = None

    if selected_conversation_id:
        try:
            selected_conversation = Conversation.objects.get(id=selected_conversation_id)
            if selected_conversation.patient == request.user or selected_conversation.doctor == request.user:
                messages = selected_conversation.messages.order_by('timestamp')
                selected_contact = selected_conversation.doctor if selected_conversation.patient == request.user else selected_conversation.patient
                selected_conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        except Conversation.DoesNotExist:
            pass

    context = {
        'contacts': contacts,
        'selected_conversation': selected_conversation,
        'messages': messages,
        'selected_contact': selected_contact,
        'doctor_or_patient': 'doctor' if hasattr(request.user, 'doctor_profile') else 'patient'
    }
    return render(request, 'message.html', context)

@login_required
def send_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            conversation_id = data.get('conversation_id')
            content = data.get('content')
            replace_messages = data.get('replace', False)  
            if not content or not conversation_id:
                return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)

            conversation = Conversation.objects.get(id=conversation_id)
            if conversation.patient != request.user and conversation.doctor != request.user:
                return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

            if replace_messages:
                conversation.messages.all().delete()

            new_messages = Message.objects.for_receiver(request.user).filter(is_read=False).count()

            return JsonResponse({
                'status': 'success',
                'message': {
                    'id': new_messages.id,
                    'content': new_messages.content,
                    'timestamp': new_messages.timestamp.strftime('%I:%M %p'),
                    'sender': new_messages.sender.username,
                }
            })
        except Conversation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Conversation not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone

@login_required
def clinic_dashboard(request):

    user = request.user
    if not user.is_clinic:
        return redirect("home")

    clinics = Clinic.objects.filter(admin=user)

    clinic_id = request.GET.get('clinic_id')
    clinic = clinics.filter(id=clinic_id).first() if clinic_id else clinics.first()

    if not clinic:
        return render(request, "clinic/dashboard.html", {
            "error": "No clinic found.",
            "clinics": clinics
        })

    doctor_list = list(clinic.assigned_doctors.all())

    if clinic.doctor and clinic.doctor not in doctor_list:
        doctor_list.append(clinic.doctor)

    total_doctors = len(doctor_list)
    appointments = Appointment.objects.filter(
        doctor__in=doctor_list,
        payment_status="paid"
    ).distinct()

    total_appointments = appointments.count()

    upcoming_appointments = appointments.filter(
        appointment_datetime__gte=timezone.now()
    ).count()

    approved = appointments.filter(status__iexact="accepted").count()
    pending = appointments.filter(status__iexact="pending").count()


    total_patients = Patient.objects.filter(
        appointments__in=appointments
    ).distinct().count()

    
    reviews_count = SubmitReview.objects.filter(
        doctor__in=doctor_list
    ).count()

    context = {
        "clinic": clinic,
        "clinics": clinics,
        "doctor_list": doctor_list,
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "upcoming_appointments": upcoming_appointments,
        "total_appointments": total_appointments,
        "reviews_count": reviews_count,
        "Approved": approved,
        "pending": pending,
        "is_clinic_owner": True,
    }

    return render(request, "clinic/dashboard.html", context)


@login_required
def clinic_appointment_list(request):
    user = request.user
    clinics = Clinic.objects.filter(admin=user)

    if not clinics.exists():
        messages.error(request, "You are not assigned to any clinic.")
        return redirect('home')

    clinic_id = request.GET.get('clinic_id')
    clinic = clinics.filter(id=clinic_id).first() if clinic_id else clinics.first()

    if not clinic:
        messages.error(request, "Invalid clinic selection.")
        return redirect('home')


    doctors_in_clinic = Doctor.objects.filter(clinics=clinic).distinct()

    now = timezone.now()

    all_appointments = Appointment.objects.filter(
        doctor__in=doctors_in_clinic,payment_status="paid"
    ).distinct()

    past_appointments = []
    upcoming_appointments = []

    for appt in all_appointments:
        if timezone.is_naive(appt.appointment_datetime):
            appt.appointment_datetime = timezone.make_aware(appt.appointment_datetime)

        if appt.appointment_datetime < now:
            past_appointments.append(appt)
        else:
            upcoming_appointments.append(appt)

    upcoming_appointments.sort(key=lambda x: x.appointment_datetime)
    past_appointments.sort(key=lambda x: x.appointment_datetime, reverse=True)


    paginator_upcoming = Paginator(upcoming_appointments, 10)
    paginator_past = Paginator(past_appointments, 10)

    upcoming_page = request.GET.get('upcoming_page')
    past_page = request.GET.get('past_page')

    upcoming_page_obj = paginator_upcoming.get_page(upcoming_page)
    past_page_obj = paginator_past.get_page(past_page)

    return render(request, 'clinic/clinic_appointments.html', {
        'clinic': clinic,
        'clinics': clinics,
        'upcoming_page_obj': upcoming_page_obj,
        'past_page_obj': past_page_obj,
        'doctor': getattr(user, 'doctor_profile', None),
    })

from .models import Clinic, ClinicListing, ClinicService
@login_required
def clinic_listing(request):
    user = request.user
    clinics = Clinic.objects.filter(admin=user)
    clinic_id = request.GET.get('clinic_id')
    clinic = clinics.filter(id=clinic_id).first() if clinic_id else clinics.first()

    if not clinic:
        return redirect('some_error_page')

    if request.method == 'POST':
        ClinicListing.objects.filter(clinic=clinic).delete()
        ClinicService.objects.filter(clinic=clinic).delete()

        treatments = request.POST.getlist('treatment[]')
        prices = request.POST.getlist('price[]')

        for treatment, price in zip(treatments, prices):
            if treatment and price:
                ClinicListing.objects.create(clinic=clinic, treatment=treatment, price=price)
                ClinicService.objects.create(clinic=clinic, name=treatment, price=price)

        return redirect(f"{request.path}?clinic_id={clinic.id}")

    pricing = ClinicListing.objects.filter(clinic=clinic)
    print("Pricing in template:", pricing)

    return render(request, 'clinic/clinic_listing.html', {
        'pricing': pricing,
        'clinic': clinic,
        'clinics': clinics,
    })

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum
from doctorsapp.models import Clinic, Appointment

from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from datetime import datetime
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.db.models.functions import TruncMonth


@login_required
def clinic_revenue_dashboard(request, clinic_id):
    clinic = get_object_or_404(Clinic, id=clinic_id)

    # 🔐 Security check
    if request.user != clinic.admin:
        raise PermissionDenied

    appointments = Appointment.objects.filter(
        doctor__clinics=clinic,
        payment_status="paid"
    ).select_related('doctor', 'patient')

    total_revenue = appointments.aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    total_appointments = appointments.count()
    total_doctors = clinic.assigned_doctors.count()
    total_patients = appointments.values("patient").distinct().count()

    # 📊 Monthly Revenue
    monthly_data = (
        appointments
        .annotate(month=TruncMonth("appointment_datetime"))
        .values("month")
        .annotate(total=Sum("total_amount"))
        .order_by("month")
    )

    months = [m["month"].strftime("%b %Y") for m in monthly_data]
    monthly_revenue = [float(m["total"]) for m in monthly_data]

    # 👨‍⚕️ Doctor Revenue
    doctor_data = (
        appointments
        .values("doctor__user__first_name", "doctor__user__last_name")
        .annotate(total=Sum("total_amount"))
    )

    doctor_names = [
        f"{d['doctor__user__first_name']} {d['doctor__user__last_name']}"
        for d in doctor_data
    ]

    doctor_revenue = [float(d["total"]) for d in doctor_data]

    return render(request, "clinic/clinic_revenue.html", {
        "clinic": clinic,
        "appointments": appointments,
        "total_revenue": total_revenue,
        "total_appointments": total_appointments,
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "months": months,
        "monthly_revenue": monthly_revenue,
        "doctor_names": doctor_names,
        "doctor_revenue": doctor_revenue,
    })

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import render, get_object_or_404
from .models import Doctor, Appointment


def doctor_revenue_dashboard(request, doctor_id):

    doctor = get_object_or_404(Doctor, id=doctor_id)
    appointments = Appointment.objects.filter(
        doctor=doctor,
        payment_status="paid"
    )
    total_revenue = appointments.aggregate(
        total=Sum("total_amount")
    )["total"] or 0
    total_appointments = appointments.count()
    total_patients = appointments.values("patient").distinct().count()


    monthly_data = (
        appointments
        .annotate(month=TruncMonth("appointment_datetime"))
        .values("month")
        .annotate(total=Sum("total_amount"))
        .order_by("month")
    )

    months = [m["month"].strftime("%b") for m in monthly_data]
    monthly_revenue = [float(m["total"]) for m in monthly_data]

    context = {
        "doctor": doctor,
        "appointments": appointments[:10],
        "total_revenue": total_revenue,
        "total_appointments": total_appointments,
        "total_patients": total_patients,
        "months": months,
        "monthly_revenue": monthly_revenue,
    }

    return render(request, "doctorrevenue_dashboard.html", context)




from django.http import JsonResponse
from .models import SubmitReview

def get_reviews(request):
    reviews = SubmitReview.objects.all()

    data = []
    for r in reviews:
        data.append({
            "name": r.name if r.name else "Anonymous",
            "role": "Patient",
            "message": r.message,   # ✅ FIXED
            "rating": r.rating,
            "doctor": str(r.doctor) if r.doctor else ""
        })

    return JsonResponse(data, safe=False)