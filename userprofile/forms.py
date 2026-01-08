from django import forms
from .models import RegistrationRequest
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    middle_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    country_code = forms.CharField(max_length=8, initial='+1')
    phone = forms.CharField(max_length=30)
    ssn = forms.CharField(max_length=20, required=False)
    username = forms.CharField(max_length=150)
    # Collect password so we can create a Django User at registration
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    id_type = forms.CharField(max_length=50)
    id_front = forms.FileField(required=False)
    id_back = forms.FileField(required=False)

    def clean(self):
        cleaned = super().clean()
        country_code = cleaned.get('country_code')
        ssn = cleaned.get('ssn')
        pw = cleaned.get('password')
        pw2 = cleaned.get('confirm_password')
        if pw and pw2 and pw != pw2:
            raise ValidationError('Passwords do not match')
        # check username/email uniqueness
        username = cleaned.get('username')
        email = cleaned.get('email')
        if username and User.objects.filter(username=username).exists():
            raise ValidationError('Username already taken')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Email already registered')
        if country_code and country_code.strip() == '+1' and not ssn:
            raise ValidationError('SSN is required for +1 phone numbers')

        return cleaned

    def save(self):
        # Create RegistrationRequest instance; do NOT store raw passwords
        data = self.cleaned_data
        import random
        from django.contrib.auth.models import User

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # create Django user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = data.get('first_name')
        user.last_name = data.get('last_name')
        user.save()

        # generate user id and accounts
        rand2 = random.randint(10, 99)
        rand6 = random.randint(100000, 999999)
        user_id = f"SKB-{rand2}-{rand6}"

        def rand_acc():
            return str(random.randint(100000000, 999999999))

        savings_acc = rand_acc()
        checking_acc = rand_acc()
        credit_acc = rand_acc()

        rr = RegistrationRequest(
            user=user,
            first_name=data.get('first_name'),
            middle_name=data.get('middle_name') or '',
            last_name=data.get('last_name'),
            email=email,
            country_code=data.get('country_code'),
            phone=data.get('phone'),
            ssn=data.get('ssn') or '',
            username=username,
            id_type=data.get('id_type') or '',
            skb_user_id=user_id,
            savings_account=savings_acc,
            checking_account=checking_acc,
            credit_account=credit_acc,
        )
        # Do not set id files here; view will attach uploaded files and save
        rr.save()
        return rr
