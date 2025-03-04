from django.db import models

class Dataset(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    zip_file = models.FileField(upload_to='datasets/')

    def __str__(self):
        return self.name
    


class Register(models.Model):
    username = models.CharField(max_length=70)
    email  = models.EmailField()
    password = models.CharField(max_length=50)