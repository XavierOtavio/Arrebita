from django.db import models

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255)
    password_hash = models.CharField(max_length=255)
    full_name = models.CharField(max_length=200)
    role = models.CharField(max_length=32)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'users'

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

# Create your models here.
