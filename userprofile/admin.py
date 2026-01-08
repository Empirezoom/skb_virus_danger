from django.contrib import admin
from .models import RegistrationRequest, CustomerProfile, Account, Message


class AccountInline(admin.TabularInline):
    model = Account
    extra = 0
    readonly_fields = ('account_number', 'created_at')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('customer_profile', 'account_type', 'account_number', 'balance', 'created_at')
    readonly_fields = ('account_number', 'created_at')
    search_fields = ('customer_profile__user__username', 'account_number')
    list_filter = ('account_type',)


@admin.register(RegistrationRequest)
class RegistrationRequestAdmin(admin.ModelAdmin):
	list_display = ('username', 'email', 'phone', 'country_code', 'ssn', 'created_at')
	readonly_fields = ('created_at',)
	search_fields = ('username', 'email', 'phone')
	actions = ['approve_and_create_user']

	def approve_and_create_user(self, request, queryset):
		from django.contrib.auth.models import User
		from django.contrib import messages
		from django.core.mail import send_mail
		from django.contrib.auth.tokens import default_token_generator
		from django.utils.http import urlsafe_base64_encode
		from django.utils.encoding import force_bytes
		from django.urls import reverse
		from .models import CustomerProfile
		import secrets

		created = 0
		skipped = 0
		for rr in queryset:
			if rr.approved:
				skipped += 1
				continue
			username = rr.username
			if User.objects.filter(username=username).exists():
				skipped += 1
				continue
			# create user with unusable password; email reset link for password setup
			user = User.objects.create_user(username=username)
			user.set_unusable_password()
			user.email = rr.email
			user.first_name = rr.first_name
			user.last_name = rr.last_name
			user.save()

			# create CustomerProfile
			skb_user_id = secrets.token_hex(20)  # 40 char
			profile = CustomerProfile.objects.create(
				user=user,
				first_name=rr.first_name,
				middle_name=rr.middle_name,
				last_name=rr.last_name,
				email=rr.email,
				country_code=rr.country_code,
				phone=rr.phone,
				ssn=rr.ssn,
				id_type=rr.id_type,
				id_front=rr.id_front,
				id_back=rr.id_back,
				skb_user_id=skb_user_id,
				approved=True
			)
			# Accounts will be created automatically via signal

			# generate password reset token link
			uid = urlsafe_base64_encode(force_bytes(user.pk))
			token = default_token_generator.make_token(user)
			# build password reset confirm url (requires auth urls included)
			reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
			reset_url = request.build_absolute_uri(reset_path)

			subject = 'Set your Skandia Bank account password'
			message = f"Hello {user.first_name},\n\nAn admin has approved your registration. Set your password using the link below:\n\n{reset_url}\n\nIf you didn't request this, ignore this email.\n"
			send_mail(subject, message, None, [user.email])

			rr.approved = True
			rr.save()
			created += 1

		self.message_user(request, f"Created {created} users and profiles, skipped {skipped} entries.")

	approve_and_create_user.short_description = 'Approve selected and create Django User accounts'


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'skb_user_id', 'email', 'phone', 'approved', 'created_at')
	readonly_fields = ('created_at',)
	search_fields = ('user__username', 'email', 'skb_user_id')
	list_filter = ('approved',)
	fieldsets = (
		(None, {'fields': ('user', 'skb_user_id', 'approved')}),
		('Personal', {'fields': ('first_name', 'middle_name', 'last_name', 'email', 'country_code', 'phone', 'ssn', 'id_type')}),
		('IDs', {'fields': ('id_front', 'id_back')}),
		('Timestamps', {'fields': ('created_at',)}),
	)
	inlines = [AccountInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ('user_id', 'sender', 'message', 'file', 'timestamp')
	readonly_fields = ('user_id', 'sender', 'message', 'file', 'timestamp')
	search_fields = ('user_id', 'message', 'sender')
	list_filter = ('sender', 'timestamp')
	
