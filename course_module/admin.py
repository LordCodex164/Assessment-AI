from django.contrib import admin
from .models import Course

# Register your models here.

models_to_register = [Course]

for model in models_to_register:
    admin.site.register(model)