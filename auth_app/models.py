# models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """
    Custom manager to handle user creation with user_type
    """
    
    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The Username field must be set')
        if not email:
            raise ValueError('The Email field must be set')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """Create regular user with user_type support"""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('user_type', 'student')
        return self._create_user(username, email, password, **extra_fields)
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'staff')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self._create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model with role-based access
    """
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('staff', 'Staff'),
    ]
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='student',
        db_index=True
    )

    
    phone_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # ✅ THIS IS THE CRITICAL LINE YOU'RE MISSING!
    objects = CustomUserManager()
    
    class Meta:
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['user_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    def is_staff_user(self):
        """Check if user is staff"""
        return self.user_type == 'staff'
    
    def is_student_user(self):
        """Check if user is student"""
        return self.user_type == 'student'