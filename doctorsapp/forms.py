from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.forms import UserCreationForm
from .models import Appointment, Patient, Doctor, Clinic, Education, Experience,TimeSlot,Service,Award,Speciality
from .models import PatientSocialLinks
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import Message
from django.utils import timezone
from django.contrib.auth.forms import PasswordChangeForm
from .models import SubmitReview 
from .models import Review
import re
from django.forms import FileInput


GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other')
]

class RegistrationForm(forms.Form):
    user_type = forms.ChoiceField(choices=[('patient', 'Patient'), ('doctor', 'Doctor')], required=True)
    first_name = forms.CharField(label='First Name', max_length=100, required=True)
    last_name = forms.CharField(label='Last Name', max_length=100, required=True)
    email = forms.EmailField(required=True)
    mobile_number=forms.CharField(max_length=15,required=False)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=True)
    specialization = forms.CharField(max_length=100, required=False)
 
    terms = forms.BooleanField(required=True)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        user_type = cleaned_data.get('user_type')
        specialization = cleaned_data.get('specialization')
        

        if password != confirm_password:
            raise ValidationError("Passwords do not match.")

        if user_type == 'doctor':
            if not specialization:
                raise ValidationError("Specialization is required for doctors.")
       

class LoginForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

class AppointmentForm(forms.ModelForm):
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.filter(is_available=True),
        empty_label="Select a Doctor"
    )
    time_slot = forms.ModelChoiceField(
        queryset=TimeSlot.objects.all(),
        empty_label="Select a time slot",
        required=True
    )
    appointment_datetime = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'min': timezone.now().strftime('%Y-%m-%dT%H:%M')}),
        label="Appointment Date and Time"
    )
    appointment_mode = forms.ChoiceField(
        choices=[('offline', 'Offline'), ('online', 'Online')],
        widget=forms.RadioSelect,
        label="Appointment Type",
        required=True
    )
    zoom_link = forms.URLField(required=False, label="Zoom Meeting Link")
    class Meta:
        model = Appointment
        fields = [
            'patient', 'doctor', 'time_slot', 'appointment_datetime',
            'appointment_type', 'status', 'payment_status',
            'fee', 'total_amount', 'appointment_notes', 'appointment_mode'
        ]

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        time_slot = cleaned_data.get('time_slot')
        appointment_datetime = cleaned_data.get('appointment_datetime')

  
        if appointment_datetime and appointment_datetime < timezone.now():
            raise forms.ValidationError("Cannot book appointments in the past.")

        if doctor and time_slot and appointment_datetime:
            if time_slot.doctor != doctor:
                raise forms.ValidationError("Selected time slot does not belong to the chosen doctor.")

            if not (time_slot.start_time <= appointment_datetime <= time_slot.end_time):
                raise forms.ValidationError("Appointment time must be within the selected time slot.")

            conflict = Appointment.objects.filter(
                doctor=doctor,
                appointment_datetime=appointment_datetime,
                status__in=['pending', 'confirmed']
            ).exclude(id=self.instance.id if self.instance else None)
            if conflict.exists():
                raise forms.ValidationError("This time slot is already booked.")

        return cleaned_data


class DoctorProfileForm(forms.ModelForm):
    
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput(), required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = Doctor
        fields = [
            'profile_image', 'first_name', 'last_name', 'email', 
            'specialization','mobile_number', 'gender',
            'date_of_birth', 'biography', 'Address1', 'Address2', 'city', 'state',
            'zip_code', 'country','qualification',
            'facebook_url', 'twitter_url', 'google_plus_url', 'instagram_url',
            
        ]
        widgets = {
            'available_days': forms.TextInput(attrs={'placeholder': 'e.g., Monday, Wednesday, Friday'}),
            'start_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'end_time': forms.TimeInput(format='%H:%M', attrs={'type': 'time'}),
            'facebook_url': forms.URLInput(attrs={'placeholder': 'https://facebook.com'}),
            'twitter_url': forms.URLInput(attrs={'placeholder': 'https://twitter.com'}),
            'linkedin_url': forms.URLInput(attrs={'placeholder': 'https://linkedin.com'}),
            'instagram_url': forms.URLInput(attrs={'placeholder': 'https://instagram.com'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        doctor = super().save(commit=False)
        if commit:
            doctor.save()
            user = doctor.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']

            password = self.cleaned_data.get('password')
            if password:
                user.set_password(password)

            user.save()
        return doctor

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password or confirm_password:
            if password != confirm_password:
                self.add_error("confirm_password", "Passwords do not match.")
                
    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')

        if isinstance(image, InMemoryUploadedFile):
             if image.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 2MB )")
        return image
  

class ClinicForm(forms.ModelForm):
    specifications = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        help_text="Enter comma-separated values (e.g., Parking, Pharmacy, Wheelchair Access)."
    )
    awards = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        help_text="Enter in the format: Award Title (Year), separated by commas. Example: Best Clinic (2020), Excellence in Service (2022)"
    )

    class Meta:
        model = Clinic
        fields = [
            'name', 'tagline', 'description', 'overview', 'specifications',
            'services', 'awards', 'image', 'phone', 'email', 'fax',
            'website', 'address', 'working_hours', 'map_lat', 'map_lng', 'map_marker','about'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'tagline': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'overview': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'services': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'image': FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'working_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'map_lat': forms.TextInput(attrs={'class': 'form-control'}),
            'map_lng': forms.TextInput(attrs={'class': 'form-control'}),
            'map_marker': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_specifications(self):
        data = self.cleaned_data.get('specifications', '')
        return [item.strip() for item in data.split(',') if item.strip()]

    def clean_awards(self):
        data = self.cleaned_data.get('awards', '')
        awards_list = []
        matches = re.findall(r'(.*?)\s*\((\d{4})\)', data)
        for title, year in matches:
            awards_list.append({'title': title.strip(), 'year': int(year)})
        return awards_list
    
from .models import Branch

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'address', 'phone', 'map_link']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter branch name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter address'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional phone'}),
            'map_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Optional map link'}),
        }

class EducationForm(forms.ModelForm):
    class Meta:
        model = Education
        fields = ['id', 'degree', 'institute', 'passing_year']


class ExperienceForm(forms.ModelForm):
    class Meta:
        model = Experience
        fields = ['id', 'hospital_name', 'designation', 'from_date', 'to_date']

class AwardForm(forms.ModelForm):
    class Meta:
        model = Award
        fields = ['name', 'year']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SpecialityForm(forms.ModelForm):
    class Meta:
        model = Speciality
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Speciality Name'}),
        }

class DoctorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    specialization = forms.ChoiceField(choices=Doctor)
    phone_number = forms.CharField(max_length=15, required=True)
    address = forms.CharField(widget=forms.Textarea, required=True)
    profile_image = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            doctor = Doctor.objects.create(
                user=user,
                specialization=self.cleaned_data['specialization'],
                phone_number=self.cleaned_data['phone_number'],
                address=self.cleaned_data['address']
            )
            if 'profile_image' in self.cleaned_data and self.cleaned_data['profile_image']:
                doctor.profile_image = self.cleaned_data['profile_image']
                doctor.save()
        
        return user
    
class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'price', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter service name'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),


        }

class PatientForm(forms.ModelForm):

    GENDER_CHOICES = [
        ('', 'Select Gender'),
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    MARITAL_STATUS_CHOICES = [
        ('', 'Select Marital Status'),
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed'),
    ]
    BLOOD_GROUP_CHOICES = [
        ('', 'Select Blood Group'),
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    class Meta:
        model = Patient
        fields = [
           'profile_image', 'first_name', 'last_name', 'email', 'date_of_birth', 'gender', 
            'mobile_number', 'age', 'location',
            'address', 'blood_group', 'marital_status', 'doctor_note',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(choices=[('', 'Select Gender')] + list(Patient.GENDER_CHOICES)),
            'blood_group': forms.Select(choices=[('', 'Select Blood Group')] + list(Patient.BLOOD_GROUP_CHOICES)),
            'marital_status': forms.Select(choices=[('', 'Select Marital Status')] + list(Patient.MARITAL_STATUS_CHOICES)),
            'doctor_note': forms.Textarea(attrs={'placeholder': 'Write your note...', 'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_profile_image(self):
        image = self.cleaned_data.get('profile_image')

        if isinstance(image, InMemoryUploadedFile):
             if image.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Image file too large ( > 2MB )")
        return image
  

class SocialLinksForm(forms.ModelForm):
    class Meta:
        model = PatientSocialLinks
        fields = ['facebook', 'twitter', 'linkedin', 'instagram']
        widgets = {
            'facebook': forms.URLInput(attrs={'placeholder': 'https://facebook.com'}),
            'twitter': forms.URLInput(attrs={'placeholder': 'https://twitter.com'}),
            'linkedin': forms.URLInput(attrs={'placeholder': 'https://linkedin.com'}),
            'instagram': forms.URLInput(attrs={'placeholder': 'https://instagram.com'}),
        }

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type something'}),
        }

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput, label="Old Password")
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Old password is incorrect.")
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("New passwords do not match.")
        return cleaned_data
    

class TimeSlotForm(forms.ModelForm):
    class Meta:
        model = TimeSlot
        fields = ['day_of_week', 'start_time', 'end_time', 'is_available']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'day_of_week': forms.Select(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(TimeSlotForm, self).__init__(*args, **kwargs)
     
        self.fields['day_of_week'].choices = [
            (i, day) for i, day in enumerate(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        ]

class CustomPasswordChangeForm(PasswordChangeForm):
    
    old_password = forms.CharField(
        label="Old Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )


class SubmitReviewForm(forms.ModelForm):
    class Meta:
        model = SubmitReview
        fields = ['doctor', 'rating', 'title', 'name', 'email', 'message', 'terms_accepted']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'terms_accepted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

from .models import Clinic

class ClinicContactForm(forms.ModelForm):
    class Meta:
        model = Clinic
        fields = [
            'working_hours', 'address', 'phone', 'fax',
            'email', 'website', 'facebook', 'instagram',
            'twitter', 'google_plus'
        ]
        widgets = {
            'working_hours': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'fax': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'google_plus': forms.URLInput(attrs={'class': 'form-control'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }