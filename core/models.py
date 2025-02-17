from django.db import models
from django.contrib.auth.models import User, AbstractUser, BaseUserManager
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.conf import settings
from cloudinary.models import CloudinaryField

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)
        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    def __str__(self):
        return self.username

class WasteReport(models.Model):
    WASTE_TYPES = [
        ('plastic', 'Plastic'),
        ('organic', 'Organic'),
        ('electronic', 'Electronic'),
        ('hazardous', 'Hazardous'),
        ('metal', 'Metal'),
        ('glass', 'Glass'),
        ('other', 'Other')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPES)
    quantity = models.FloatField()
    
    # Location fields
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    address = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_team = models.ForeignKey(
        'CleanupTeam',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class WasteReportMedia(models.Model):
    MEDIA_TYPES = [
        ('image', 'Image'),
        ('video', 'Video')
    ]
    
    waste_report = models.ForeignKey(WasteReport, related_name='media', on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    file = CloudinaryField(
        'waste_reports',
        resource_type='auto',
        folder='waste_reports'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

class CleanupTeam(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)

class Pickup(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    waste_report = models.ForeignKey(WasteReport, on_delete=models.CASCADE)
    scheduled_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class EducationalResource(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('waste_report', 'Waste Report'),
        ('pickup_request', 'Pickup Request'),
        ('status_update', 'Status Update'),
        ('pickup_status', 'Pickup Status'),
        ('educational', 'Educational Content')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    reference_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} - {self.title}"

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    profile_picture = CloudinaryField(
        'profile_pictures',
        folder='profile_pics',
        null=True,
        blank=True
    )

class PickupRequest(models.Model):
    WASTE_TYPES = [
        ('plastic', 'Plastic'),
        ('organic', 'Organic'),
        ('medical', 'Medical'),
        ('electronic', 'Electronic'),
        ('hazardous', 'Hazardous'),
        ('general', 'General'),
        ('other', 'Other')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    waste_type = models.CharField(max_length=20, choices=WASTE_TYPES)
    pickup_date = models.DateField()
    pickup_time = models.TimeField()
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    instructions = models.TextField(blank=True)
    quantity_estimate = models.FloatField(help_text="Estimated quantity in kg")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    collector = models.ForeignKey(
        'WasteCollector',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Validate that pickup date is not in the past
        if self.pickup_date < timezone.now().date():
            raise ValidationError({'pickup_date': 'Pickup date cannot be in the past'})

class WasteCollector(models.Model):
    name = models.CharField(max_length=200)
    vehicle_number = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    is_available = models.BooleanField(default=True)
    current_location_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    current_location_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

class EducationalContent(models.Model):
    CONTENT_TYPES = [
        ('article', 'Article'),
        ('video', 'Video'),
        ('pdf', 'PDF'),
        ('quiz', 'Quiz')
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    description = models.TextField()
    content = models.TextField()  # For articles
    video_url = models.URLField(blank=True, null=True)  # For videos
    file = CloudinaryField(
        'educational_content',
        resource_type='auto',
        folder='educational_content',
        null=True,
        blank=True
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    views = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class Quiz(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    question = models.TextField()
    correct_answer = models.CharField(max_length=200)
    option1 = models.CharField(max_length=200)
    option2 = models.CharField(max_length=200)
    option3 = models.CharField(max_length=200)
    explanation = models.TextField(blank=True)

class UserQuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.PositiveIntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

class ForumTopic(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ForumComment(models.Model):
    topic = models.ForeignKey(ForumTopic, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
