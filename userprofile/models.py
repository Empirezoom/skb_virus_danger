from django.db import models
from django.conf import settings
import secrets
from django.db.models.signals import post_save
from django.dispatch import receiver


class RegistrationRequest(models.Model):
    # Link to the created Django user (if created)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    country_code = models.CharField(max_length=8, default='+1')
    phone = models.CharField(max_length=30)
    ssn = models.CharField(max_length=20, blank=True, null=True)
    username = models.CharField(max_length=150)
    # approved indicates admin has processed the request (legacy field)
    approved = models.BooleanField(default=False)
    id_type = models.CharField(max_length=50, blank=True)
    id_front = models.FileField(upload_to='ids/', blank=True, null=True)
    id_back = models.FileField(upload_to='ids/', blank=True, null=True)
    # Generated identifiers/accounts
    skb_user_id = models.CharField(max_length=40, blank=True)
    savings_account = models.CharField(max_length=32, blank=True)
    checking_account = models.CharField(max_length=32, blank=True)
    credit_account = models.CharField(max_length=32, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.email})"


class Account(models.Model):
    ACCOUNT_TYPES = [
        ('savings', '💰Savings'),
        ('checking', '🏦Checking'),
        ('credit_card', '💳Credit Card'),
    ]
    
    customer_profile = models.ForeignKey('CustomerProfile', on_delete=models.CASCADE, related_name='accounts')
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    account_number = models.CharField(max_length=32, unique=True, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.account_number:
            if self.account_type == 'savings':
                self.account_number = '003' + ''.join(secrets.choice('0123456789') for _ in range(9))
            elif self.account_type == 'checking':
                self.account_number = '282' + ''.join(secrets.choice('0123456789') for _ in range(6))
            elif self.account_type == 'credit_card':
                # Generate 16-digit number
                number = ''.join(secrets.choice('0123456789') for _ in range(16))
                self.account_number = f"{number[:4]}-{number[4:8]}-{number[8:12]}-{number[12:]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_profile.user.username} - {self.account_type} ({self.account_number[-4:]})"


class CustomerProfile(models.Model):
    """Persistent profile/account record linked to Django's User.

    Stores personal data, uploaded ID files, generated SKB id.
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=150)
    middle_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150)
    email = models.EmailField()
    country_code = models.CharField(max_length=8, default='+1')
    phone = models.CharField(max_length=30)
    ssn = models.CharField(max_length=20, blank=True, null=True)
    approved = models.BooleanField(default=False)
    userstatus = models.BooleanField(default=True)  # True = Active, False = Blocked
    user_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    id_type = models.CharField(max_length=50, blank=True)
    id_front = models.FileField(upload_to='ids/', blank=True, null=True)
    id_back = models.FileField(upload_to='ids/', blank=True, null=True)
    skb_user_id = models.CharField(max_length=40, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.skb_user_id or 'no-id'}"

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
        ('payment', 'Payment'),
    ]
    
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account} - {self.transaction_type} - ${self.amount}"

class Recipient(models.Model):
    customer_profile = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='recipients')
    name = models.CharField(max_length=255)
    user_id = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.customer_profile.user.username} - {self.name}"

class Payment(models.Model):
    TO_TYPE_CHOICES = [
        ('internal', 'Internal Transfer'),
        ('external', 'External Payment'),
    ]
    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Pending', 'Pending'),
    ]
    
    customer_profile = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='payments')
    from_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='payments_from')
    to_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='payments_to', blank=True, null=True)
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, blank=True, null=True)
    to_type = models.CharField(max_length=20, choices=TO_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=50)
    note = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Completed')

    def __str__(self):
        return f"{self.customer_profile.user.username} - ${self.amount} - {self.status}"

class ScheduledPayment(models.Model):
    TO_TYPE_CHOICES = [
        ('internal', 'Internal Transfer'),
        ('external', 'External Payment'),
    ]
    RECURRING_CHOICES = [
        ('none', 'None'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    customer_profile = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='scheduled_payments')
    from_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='scheduled_from')
    to_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='scheduled_to', blank=True, null=True)
    recipient = models.ForeignKey(Recipient, on_delete=models.CASCADE, blank=True, null=True)
    to_type = models.CharField(max_length=20, choices=TO_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=50)
    note = models.TextField(blank=True)
    schedule_date = models.DateField()
    recurring = models.CharField(max_length=20, choices=RECURRING_CHOICES, default='none')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')

    def __str__(self):
        return f"{self.customer_profile.user.username} - ${self.amount} - {self.schedule_date}"

class Message(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]
    
    user_id = models.CharField(max_length=100)  # the skb_user_id
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField(blank=True)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user_id} - {self.sender} - {self.timestamp}"

@receiver(post_save, sender=CustomerProfile)
def create_accounts(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(customer_profile=instance, account_type='savings')
        Account.objects.create(customer_profile=instance, account_type='checking')
        Account.objects.create(customer_profile=instance, account_type='credit_card')


