from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Message(models.Model):
    user_id = models.CharField(max_length=128, db_index=True)
    sender = models.CharField(max_length=16, choices=(("user","user"),("admin","admin")))
    message = models.TextField(blank=True)
    file = models.FileField(upload_to="chat_files/", blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "sender": self.sender,
            "message": self.message,
            "file_url": self.file.url if self.file else None,
            "file_name": self.file.name.split("/")[-1] if self.file else None,
            "timestamp": int(self.timestamp.timestamp() * 1000),
            "read": self.read,
        }

class BalanceRequest(models.Model):
    user_id = models.CharField(max_length=128)
    account_name = models.CharField(max_length=128)
    mode = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)

class WithdrawalRequest(models.Model):
    user_id = models.CharField(max_length=128)
    bank = models.CharField(max_length=128)
    account = models.CharField(max_length=128)
    routing = models.CharField(max_length=64)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    otp = models.CharField(max_length=64, blank=True, null=True)
    status = models.CharField(max_length=16, default='pending', choices=(('pending','pending'),('completed','completed'),('cancelled','cancelled')))
    created_at = models.DateTimeField(default=timezone.now)

class PaymentDetail(models.Model):
    user_id = models.CharField(max_length=128)
    mode = models.CharField(max_length=64)
    account = models.CharField(max_length=255)
    transaction_id = models.CharField(max_length=128)
    created_at = models.DateTimeField(default=timezone.now)

class OTPLog(models.Model):
    user_id = models.CharField(max_length=128)
    otp = models.CharField(max_length=32)
    created_at = models.DateTimeField(default=timezone.now)

# Create your models here.

class SkBank(models.Model):
    name = models.CharField( max_length=50)
    slug = models.SlugField(unique=True)
    svg = models.TextField(max_length=50, default='hd',blank=True, null=True)
    email = models.EmailField( max_length=254)
    phone = models.CharField( max_length=15, blank=True, null=True)
    address = models.CharField( max_length=50)
    copyright = models.CharField( max_length=750)
    favicon = models.ImageField(upload_to='favicons/', blank=True, null=True)
    banner = models.ImageField(upload_to='banners/', blank=True, null=True)

    def __str__(self):
        return self.name
    class Meta:
        db_table = 'CompanyProfile'
        managed = True
        verbose_name = 'CompanyProfile'
        verbose_name_plural = 'CompanyProfile'