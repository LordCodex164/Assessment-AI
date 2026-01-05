from django.db import models

# Create your models here.

# create an exam model

### don't forget to add throttling

class Course(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    code = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.code} - {self.name}"