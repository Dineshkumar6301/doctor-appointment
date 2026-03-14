from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
   
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('doctors/dashboard/', views.doctor_dashboard_view, name='doctor_dashboard'),
    path('my-patients/', views.my_patients, name='my_patients'),
    path('patients/add/', views.add_patient, name='add_patient'),
    path('doctors/', views.doctor_list_view, name='doctor_list'),
    path('doctor/<int:doctor_id>/', views.doctor_detail_view, name='doctor_detail'), 
    path('edit/<int:patient_id>/', views.edit_patient, name='edit_patient'),
    path('delete/<int:patient_id>/', views.delete_patient, name='delete_patient'),
    path('patients/dashboard/', views.patient_dashboard_view, name='patient_dashboard'),
    path('appointments/<int:appointment_id>/details/', views.appointment_detail_view, name='appointment_detail_viwe'),
    path('appointments/', views.doctor_appointment_list, name='doctor_appointment_list'),
    path('doctors/add-appointment/', views.add_appointment, name='add_appointment'),
    path('appointment/edit/<int:appointment_id>/', views.edit_appointment, name='edit_appointment'),
    path('appointment/delete/<int:appointment_id>/', views.delete_appointment, name='delete_appointment'),
    path('appointment/accept/<int:appointment_id>/', views.accept_appointment, name='accept_appointment'),
    path('appointment/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('add-patient/', views.add_patient, name='add_patient'),
    path('my_profile/', views.my_profile, name='my_profile'),
    path('add-listing/', views.add_listing, name='add_listing'),
    path('schedule-timing/', views.schedule_timing_view, name='schedule_timing'),
    path('calendar-events/', views.calendar_events, name='calendar_events'),
    path('review/<doctor_id>/', views.doctor_reviews, name='doctor_reviews'),
    path('change-password/', views.change_password, name='change_password'),
    path('profile/', views.profile, name='profile'),
    path('change-password2/', views.change_password2, name='change_password2'),
    path('submit', views.submit_review, name='submit_review'),
    path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),
    path('confirm/<int:appointment_id>/', views.confirm_appointment, name='confirm_appointment'),
    path("razorpay/order/<int:appointment_id>/", views.create_razorpay_order, name="razorpay_order"),
   
    path('schedule/time-slot/', views.add_or_edit_time_slot, name='add_time_slot'),
    path('delete-time-slot/<int:slot_id>/', views.delete_time_slot, name='delete_time_slot'),
    path('message/', views.messages_view, name='messages'),
    path('favourite-doctors/', views.favourite_doctors, name='favourite_doctors'),
    path('messages-2/', views.message_dashboard, name='message_dashboard'),
    path('send-message/', views.send_message, name='send_message'),
    path('contact/',views.contact_us,name='contact'),
    path('about/',views.about_us,name='about' ),
    path('clinic/<int:clinic_id>/', views.clinic, name='clinic'),
    path("edit-clinic/<int:clinic_id>/", views.edit_clinic, name="edit_clinic"),
    path('clinic/<int:clinic_id>/add-branch/', views.add_branch, name='add_branch'),
    path('branch/<int:branch_id>/edit/', views.edit_branch, name='edit_branch'),
    path('branch/<int:branch_id>/delete/', views.delete_branch, name='delete_branch'),
    path('clinic/<int:clinic_id>/edit-overview/', views.edit_clinic_overview, name='edit_clinic_overview'),
    path('clinic/image/<int:image_id>/delete/', views.delete_gallery_image, name='delete_gallery_image'),
    path('Clinic_list/', views.Clinic_list, name='Clinic_list'),
    path('clinic/<int:clinic_id>/update-contact/', views.update_clinic_contact, name='update_clinic_contact'),
    path('search/', views.search_results, name='search_results'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path("doctor/<int:doctor_id>/available-slots/",views.get_available_slots,name="get_available_slots"),
    path(
    "appointment/update-status/<int:appointment_id>/",
    views.update_appointment_status,
    name="update_appointment_status"
    ),
    path(
        "complete-appointment/<int:appointment_id>/",
        views.complete_appointment,
        name="complete_appointment"
    ),
    path(
        "clinic/<int:clinic_id>/revenue/",
        views.clinic_revenue_dashboard,
        name="clinic_revenue"
    ),
    path(
        "doctorrevenue-dashboard/<int:doctor_id>/",
        views.doctor_revenue_dashboard,
        name="doctorrevenue_dashboard"
    ),
    path('clinics/dashboard/', views.clinic_dashboard, name='clinic_admin_dashboard'),
    path('clinics/appointments/', views.clinic_appointment_list, name='clinic_appointment_list'),
    path('clinics/listings/', views.clinic_listing, name='clinic_listing'),

    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)