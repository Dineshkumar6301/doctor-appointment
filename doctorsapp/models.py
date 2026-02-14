from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.crypto import get_random_string
from django.utils import timezone
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import date, datetime


GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True.'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    is_doctor = models.BooleanField(default=False)
    is_patient = models.BooleanField(default=False)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email or f"User {self.id}"
    
    def save(self, *args, **kwargs):
        if self.is_doctor:
            self.is_staff = True  
        super().save(*args, **kwargs)

class Doctor(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    doctor_id = models.CharField(max_length=10, unique=True, editable=False)
    qualification= models.CharField(max_length=255, default='')
    clinics = models.ManyToManyField('Clinic', related_name='assigned_doctors', blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    specialization = models.CharField(max_length=50, null=False, blank=False)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    biography = models.TextField(blank=True)
    specialities_description = models.TextField(blank=True)
    Address1 = models.CharField(max_length=255, null=True, blank=True)
    Address2 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, null=True ,blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    profile_image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    facebook_url = models.URLField(blank=True,null =True)
    twitter_url = models.URLField(blank=True,null=True)
    google_plus_url = models.URLField(blank=True,null=True)
    instagram_url = models.URLField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank = True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    total_reviews = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    is_verified = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    review_count = models.IntegerField(default=0)
    location = models.CharField(max_length=255,blank = True,null =True)

    @property
    def availability_status(self):
        return "24/7 Available" if self.is_available else "Not Available"

    def save(self, *args, **kwargs):
        if not self.doctor_id:
            self.doctor_id = 'DOC-' + get_random_string(6, '0123456789')
        super().save(*args, **kwargs)


    def get_full_name(self):
        if self.user:
            full_name = self.user.get_full_name()
            if full_name.strip():
                return full_name
            return self.user.email or self.user.username
        return f"Doctor {self.doctor_id}"

    def __str__(self):
        return self.get_full_name()
    @property
    def star_range(self):
        return range(round(self.average_rating or 0))


class Clinic(models.Model): 
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='owned_clinics')
    name = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    fax = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    tagline = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='clinic_images/', blank=True, null=True)
    gallery_images = models.JSONField(default=list, blank=True, null=True)
    overview = models.TextField(blank=True, null=True)
    specifications = models.JSONField(default=list, blank=True,null =True)
    services = models.JSONField(default=list, blank=True,null =True)
    awards = models.JSONField(default=list, blank=True, null=True)
    about = models.TextField(blank=True, null=True)
    working_hours = models.CharField(max_length=255, blank=True, null=True)
    map_lat = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    map_lng = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    map_marker = models.ImageField(upload_to='map_markers/', blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    google_plus = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name or f"Clinic #{self.pk}"
    
class Branch(models.Model):
    clinic = models.ForeignKey(Clinic, related_name='branches', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=15, blank=True, null=True)
    map_link = models.URLField(blank=True, null=True)

class GalleryImage(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name='images')  
    image = models.ImageField(upload_to='clinic_gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.clinic.name}"


class Education(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    degree = models.CharField(max_length=100, blank=True, null=True)
    institute = models.CharField(max_length=100,blank=True,null=True)
    passing_year = models.IntegerField(blank=True,null=True)

class Experience(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    hospital_name = models.CharField(max_length=100,blank=True,null=True)
    designation = models.CharField(max_length=100,blank=True,null=True)
    from_date = models.DateField(max_length=100,blank=True,null=True)
    to_date = models.DateField(max_length=100,blank=True,null=True)

class Service(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='services')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        if self.doctor and self.doctor.user:
            return f"{self.name} - {self.doctor.user.get_full_name() or self.doctor.user.username}"
        return self.name

class DoctorSpeciality(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='speciality_entries')
    name = models.CharField(max_length=100)
    years_of_experience = models.PositiveIntegerField(null=True, blank=True)  
    def __str__(self):
        return f"{self.name} ({self.years_of_experience or 0} yrs)"
    
class Award(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='awards')
    name = models.CharField(max_length=200)
    year = models.PositiveIntegerField()

class Speciality(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='specialities', null=True, blank=True) 
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Patient(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]
    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'), ('Married', 'Married'),
        ('Divorced', 'Divorced'), ('Widowed', 'Widowed'),
    ]
    STATUS_CHOICES = [
        ('Online', 'Online'), ('Offline', 'Offline'),
        ('Away', 'Away'), ('Busy', 'Busy')
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile', null=True, blank=True)
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='patients', null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    city = models.CharField(max_length=100,null=True,blank =True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    first_name = models.CharField(max_length=30,blank=True,null=True)
    last_name = models.CharField(max_length=30,blank =True,null=True)
    patient_id = models.CharField(max_length=10, editable=False, default='Temp')
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True)
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)
    doctor_note = models.TextField(blank=True)
    profile_image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Offline')
    favourites = models.ManyToManyField('Doctor', through='FavouriteDoctor', related_name='favoured_by')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    location = models.CharField(max_length=255, blank=True, null=True)
 
    def get_full_name(self):
        """Return the patient's full name"""
        first = self.first_name or ""
        last = self.last_name or ""
        full_name = f"{first} {last}".strip()
        return full_name if full_name else f"Patient #{self.pk}"
    

    def full_name(self):
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}".strip()
    
        return self.get_full_name()
   
    def calculate_age(self):
        if self.date_of_birth:
           
            if isinstance(self.date_of_birth, str):
                try:
                    self.date_of_birth = datetime.strptime(self.date_of_birth, "%Y-%m-%d").date()
                except ValueError:
                    return None  

            today = date.today()
            age = today.year - self.date_of_birth.year
            if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
                age -= 1
            return age
        return None

    def save(self, *args, **kwargs):
        
        if not self.patient_id or self.patient_id == 'Temp':
            self.patient_id = 'PAT-' + get_random_string(6, '0123456789')
    
        if self.date_of_birth:
            self.age = self.calculate_age()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        full_name = self.get_full_name()
        return full_name if full_name else f"Patient {self.patient_id}"


class PatientSocialLinks(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='social_links')
    facebook = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Social Links for {self.patient.get_full_name()}"

class TimeSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    day_of_week = models.CharField(max_length=100)  
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    def get_days_list(self):
        return [day.strip() for day in self.day_of_week.split(',') if day.strip()]


class ScheduleTiming(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.doctor.user.username} - {self.date} ({self.start_datetime.time()} to {self.end_datetime.time()})"

class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return self.title
 
class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    APPOINTMENT_TYPE_CHOICES = [
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('emergency', 'Emergency'),
    ]

    APPOINTMENT_MODE_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='appointments'
    )

    appointment_datetime = models.DateTimeField()
    date = models.DateField(null=True, blank=True)
    time = models.TimeField(null=True, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)

    is_new_patient = models.BooleanField(null=True, blank=True)

    patient_name = models.CharField(max_length=255, blank=True, null=True)
    patient_email = models.EmailField(blank=True, null=True)
    patient_mobile_number = models.CharField(max_length=20, blank=True, null=True)

    gender = models.CharField(
        max_length=6,
        choices=[('Male', 'Male'), ('Female', 'Female')],
        null=True,
        blank=True
    )

    age = models.IntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)

    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    zip_code = models.CharField(max_length=10, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    profile_image = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True
    )

    purpose = models.TextField(blank=True, null=True)
    appointment_notes = models.TextField(blank=True, null=True)
    review_text = models.TextField(blank=True, null=True)

    appointment_type = models.CharField(
        max_length=50,
        choices=APPOINTMENT_TYPE_CHOICES,
        default='consultation'
    )

    appointment_mode = models.CharField(
        max_length=10,
        choices=APPOINTMENT_MODE_CHOICES,
        default='offline'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    zoom_link = models.URLField(null=True, blank=True)
    video_link = models.URLField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.user.get_full_name()} on {self.appointment_datetime}"

    def __str__(self):
        return f"Appointment with {self.patient.user.username} on {self.appointment_date}"
    def __str__(self):
        return f"{self.patient_name} - {self.status}"
    
    def __str__(self):
        return f"Appointment with Dr. {self.doctor.user.username}" 




class ScheduleEvent(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    start = models.DateTimeField()
    end = models.DateTimeField()

    def __str__(self):
        return f"{self.title} - {self.start} to {self.end}"

class Schedule(models.Model):
    doctor = models.ForeignKey('doctorsapp.Doctor', on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.doctor.user.username} - {self.date_time} ({'Available' if self.is_available else 'Booked'})"

class FavouriteDoctor(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class DoctorListing(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    treatment = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.treatment} by Dr. {self.doctor.get_full_name()}"  


class Review(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_reviews')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_reviews', null=True, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    message = models.TextField(max_length=1000, blank=True)
    comment = models.TextField(blank=True)
    terms_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    reply = models.TextField(blank=True, null=True)
    reply_created_at = models.DateTimeField(blank=True, null=True)
    is_new = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            doctor = self.doctor
            all_reviews = Review.objects.filter(doctor=doctor)
            doctor.total_reviews = all_reviews.count()
            doctor.average_rating = all_reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
            doctor.save()

    def __str__(self):
        return f"{self.title} by {self.name}"


class SubmitReview(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    patient = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=100)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    message = models.TextField(max_length=1000)
    terms_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.name}"

    class Meta:
        ordering = ['-created_at']


class Conversation(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='patient_conversations')
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='doctor_conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('patient', 'doctor')

    def __str__(self):
        return f"Conversation between {self.patient.email} and {self.doctor.email}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, null=True)
    sender_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        null=True,
        blank=True
    )
    sender_object_id = models.PositiveIntegerField(null=True, blank=True)
    sender = GenericForeignKey('sender_content_type', 'sender_object_id')

    receiver_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='received_messages',
        null=True,
        blank=True
    )
    receiver_object_id = models.PositiveIntegerField(null=True, blank=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages',null=True,blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        sender_str = str(self.sender) if self.sender else "Unknown Sender"
        receiver_str = str(self.receiver) if self.receiver else "Unknown Receiver"
        return f"Message from {sender_str} to {receiver_str}"

    class Meta:
        ordering = ['-timestamp']