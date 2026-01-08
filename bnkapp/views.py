from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from userprofile.forms import RegistrationForm
from userprofile.models import RegistrationRequest, CustomerProfile, Account, Recipient, Payment, ScheduledPayment
from .models import Message
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse
import io
import json
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal
from datetime import date, datetime, time
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False


# @login_required(login_url='login')
def home(request):
    profile = None
    accounts = []
    recent_transactions = []
    has_unread_admin_message = False
    if request.user.is_authenticated:
        try:
            profile = CustomerProfile.objects.get(user=request.user)
            accounts = profile.accounts.all()
            # Check for unread admin messages
            has_unread_admin_message = Message.objects.filter(user_id=profile.skb_user_id, sender='admin', read=False).exists()
            # Get recent transactions: last 4 outgoing and incoming payments
            outgoing = profile.payments.all().order_by('-date')[:4]
            incoming = Payment.objects.filter(recipient__customer_profile=profile, to_type='external').order_by('-date')[:4]
            combined = []
            for p in outgoing:
                if p.to_type == 'internal':
                    desc = "🚀Sent to Internal🏦Account"
                else:
                    desc = f"🚀Sent to👤{p.recipient.name if p.recipient else 'Unknown'}"
                combined.append({
                    'date': p.date,
                    'direction': 'outgoing',
                    'amount': p.amount,
                    'description': desc
                })
            for p in incoming:
                combined.append({
                    'date': p.date,
                    'direction': 'incoming',
                    'amount': p.amount,
                    'description': f"💸Received from👤{p.customer_profile.first_name} {p.customer_profile.last_name}"
                })
            # Sort by date descending and take top 4
            combined.sort(key=lambda x: x['date'], reverse=True)
            recent_transactions = combined[:4]
        except CustomerProfile.DoesNotExist:
            pass
    return render(request, 'index.html', {'profile': profile, 'accounts': accounts, 'recent_transactions': recent_transactions, 'has_unread_admin_message': has_unread_admin_message})


@login_required(login_url='login')
def account(request):
    try:
        profile = CustomerProfile.objects.get(user=request.user)
    except CustomerProfile.DoesNotExist:
        profile = None
        # Try to get from RegistrationRequest
        try:
            rr = RegistrationRequest.objects.get(user=request.user)
            profile = rr  # Use rr as profile for accounts
        except RegistrationRequest.DoesNotExist:
            profile = None

    has_unread_admin_message = False
    if isinstance(profile, CustomerProfile):
        has_unread_admin_message = Message.objects.filter(user_id=profile.skb_user_id, sender='admin', read=False).exists()

    account_type = request.GET.get('account_type', 'checking')
    selected_account = None
    transactions = []
    if isinstance(profile, CustomerProfile):
        try:
            selected_account = Account.objects.get(customer_profile=profile, account_type=account_type)
            # Get payments involving this account
            sent_payments = Payment.objects.filter(from_account=selected_account).order_by('-date')
            received_internal = Payment.objects.filter(to_account=selected_account).order_by('-date')
            received_external = []
            if account_type == 'savings':
                received_external = Payment.objects.filter(recipient__customer_profile=profile, to_type='external').order_by('-date')
            
            combined = []
            for p in sent_payments:
                if p.to_type == 'internal':
                    desc = "🚀Sent to Internal🏦Account"
                else:
                    desc = f"🚀Sent to👤{p.recipient.name if p.recipient else 'Unknown'}"
                combined.append({
                    'date': p.date,
                    'description': desc,
                    'amount': -float(p.amount),  # Negative for sent
                    'abs_amount': float(p.amount)
                })
            for p in received_internal:
                desc = f"💸Received from Internal Account"
                combined.append({
                    'date': p.date,
                    'description': desc,
                    'amount': float(p.amount),  # Positive for received
                    'abs_amount': float(p.amount)
                })
            for p in received_external:
                desc = f"💸Received from {p.customer_profile.first_name} {p.customer_profile.last_name}"
                combined.append({
                    'date': p.date,
                    'description': desc,
                    'amount': float(p.amount),
                    'abs_amount': float(p.amount)
                })
            # Sort by date descending and take top 10
            combined.sort(key=lambda x: x['date'], reverse=True)
            transactions = combined[:10]
        except Account.DoesNotExist:
            selected_account = None

    context = {'selected_account': selected_account, 'account_type': account_type, 'transactions': transactions, 'profile': profile if isinstance(profile, CustomerProfile) else None, 'has_unread_admin_message': has_unread_admin_message}
    return render(request, 'account.html', context)


# @login_required(login_url='login')
def payments(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        profile = CustomerProfile.objects.get(user=request.user)
    except CustomerProfile.DoesNotExist:
        # Create CustomerProfile if it doesn't exist
        profile = CustomerProfile.objects.create(
            user=request.user,
            first_name=request.user.first_name or '',
            last_name=request.user.last_name or '',
            email=request.user.email or '',
            phone='',
            ssn='',
            approved=True
        )
    
    has_unread_admin_message = Message.objects.filter(user_id=profile.skb_user_id, sender='admin', read=False).exists()
    
    accounts = profile.accounts.all()
    if not accounts.exists():
        # Ensure accounts are created if missing
        Account.objects.create(customer_profile=profile, account_type='savings')
        Account.objects.create(customer_profile=profile, account_type='checking')
        Account.objects.create(customer_profile=profile, account_type='credit_card')
        accounts = profile.accounts.all()
    print("profile:", profile)
    print("accounts count:", accounts.count())
    recipients = profile.recipients.all()
    outgoing_payments = profile.payments.all().order_by('-date')[:20]  # Outgoing payments
    incoming_payments = Payment.objects.filter(recipient__customer_profile=profile, to_type='external').order_by('-date')[:20]  # Incoming to savings
    scheduled_payments = profile.scheduled_payments.all().order_by('schedule_date')
    
    # Get credit card number for PIN verification
    credit_card_account = accounts.filter(account_type='credit_card').first()
    credit_card_number = credit_card_account.account_number if credit_card_account else ''
    
    # Serialize data for JavaScript
    accounts_data = []
    for account in accounts:
        accounts_data.append({
            'id': account.id,
            'type': account.account_type.title(),
            'number': f"•••• {account.account_number[-4:]}" if account.account_number else "•••• 0000",
            'balance': float(account.balance),
            'account_number': account.account_number
        })
    print("accounts_data:", accounts_data)  # Debug print
    
    recipients_data = []
    for recipient in recipients:
        recipients_data.append({
            'id': recipient.id,
            'name': recipient.name,
            'user_id': recipient.user_id
        })
    
    payments_data = []
    # Outgoing payments
    for payment in outgoing_payments:
        to_display = ""
        if payment.to_type == 'internal':
            to_display = payment.to_account.account_type.title() if payment.to_account else "Unknown"
        else:
            to_display = payment.recipient.name if payment.recipient else "Unknown"
        
        payments_data.append({
            'id': payment.id,
            'date': payment.date.strftime('%Y-%m-%d'),
            'direction': 'outgoing',
            'from': payment.from_account.account_type.title(),
            'to': to_display,
            'amount': float(payment.amount),
            'category': payment.category,
            'note': payment.note,
            'status': payment.status,
            'recurring': 'none'
        })
    
    # Incoming payments to savings
    for payment in incoming_payments:
        sender_name = payment.customer_profile.first_name + ' ' + payment.customer_profile.last_name
        payments_data.append({
            'id': payment.id,
            'date': payment.date.strftime('%Y-%m-%d'),
            'direction': 'incoming',
            'from': sender_name,
            'to': 'Savings',
            'amount': float(payment.amount),
            'category': payment.category,
            'note': payment.note,
            'status': payment.status,
            'recurring': 'none'
        })
    
    # Sort combined payments by date descending
    payments_data.sort(key=lambda x: x['date'], reverse=True)
    payments_data = payments_data[:20]  # Limit to 20
    
    scheduled_data = []
    for sp in scheduled_payments:
        to_display = ""
        if sp.to_type == 'internal':
            to_display = sp.to_account.account_type.title() if sp.to_account else "Unknown"
        else:
            to_display = sp.recipient.name if sp.recipient else "Unknown"
        
        scheduled_data.append({
            'id': sp.id,
            'date': sp.schedule_date.strftime('%Y-%m-%d'),
            'from': sp.from_account.account_type.title(),
            'to': to_display,
            'amount': float(sp.amount),
            'category': sp.category,
            'note': sp.note,
            'status': sp.status,
            'recurring': sp.recurring
        })
    
    context = {
        'profile': profile,
        'accounts': json.dumps(accounts_data, cls=DjangoJSONEncoder),
        'recipients': json.dumps(recipients_data, cls=DjangoJSONEncoder),
        'payments': json.dumps(payments_data, cls=DjangoJSONEncoder),
        'scheduled_payments': json.dumps(scheduled_data, cls=DjangoJSONEncoder),
        'accounts_list': accounts,  # Pass queryset for template
        'credit_card_number': credit_card_number,
        'has_unread_admin_message': has_unread_admin_message
    }
    return render(request, 'payments.html', context)


@login_required
def get_accounts(request):
    """API endpoint to get user's accounts"""
    try:
        profile = CustomerProfile.objects.get(user=request.user)
        accounts = profile.accounts.all()
        accounts_data = []
        for account in accounts:
            accounts_data.append({
                'id': account.id,
                'type': account.account_type.title(),
                'number': f"•••• {account.account_number[-4:]}" if account.account_number else "•••• 0000",
                'balance': float(account.balance),
                'account_number': account.account_number
            })
        return JsonResponse({'accounts': accounts_data})
    except CustomerProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)


@login_required
def lookup_recipient(request):
    """API endpoint to lookup external recipient by user ID"""
    user_id = request.GET.get('user_id', '').strip().upper()
    if not user_id:
        return JsonResponse({'error': 'User ID required'}, status=400)
    
    try:
        recipient_profile = CustomerProfile.objects.get(skb_user_id=user_id)
        return JsonResponse({
            'found': True,
            'name': f"{recipient_profile.first_name} {recipient_profile.last_name}",
            'user_id': user_id
        })
    except CustomerProfile.DoesNotExist:
        return JsonResponse({'found': False, 'error': 'User ID not found'})


@login_required
def save_recipient(request):
    """API endpoint to save a recipient"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        profile = CustomerProfile.objects.get(user=request.user)
        
        # Parse JSON data
        data = json.loads(request.body)
        user_id = data.get('user_id', '').strip().upper()
        name = data.get('name', '').strip()
        
        if not user_id or not name:
            return JsonResponse({'error': 'User ID and name required'}, status=400)
        
        # Check if recipient already exists
        recipient, created = Recipient.objects.get_or_create(
            customer_profile=profile,
            user_id=user_id,
            defaults={'name': name}
        )
        
        if not created:
            recipient.name = name
            recipient.save()
        
        return JsonResponse({'success': True, 'recipient_id': recipient.id})
    except CustomerProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)


@login_required
def create_payment(request):
    """API endpoint to create a payment"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        profile = CustomerProfile.objects.get(user=request.user)
        
        # Accept either JSON or traditional form POST
        content_type = request.META.get('CONTENT_TYPE', '') or request.content_type or ''
        is_json = 'application/json' in content_type
        if is_json:
            data = json.loads(request.body)
        else:
            data = request.POST

        from_account_id = data.get('from_account')
        to_type = data.get('to_type')
        amount = data.get('amount')
        category = data.get('category')
        note = data.get('note', '')
        schedule_date = data.get('schedule_date')
        recurring = data.get('recurring', 'none')

        # For external payments
        recipient_user_id = data.get('recipient_user_id')
        to_account_id = data.get('to_account')
        
        # Validate required fields
        if not all([from_account_id, to_type, amount, category]):
            error_msg = "Missing required fields"
            if is_json:
                return JsonResponse({'error': error_msg}, status=400)
            else:
                messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                return redirect('payments')
        
        try:
            amount = Decimal(amount)
            if amount <= 0:
                error_msg = "Invalid amount"
                if is_json:
                    return JsonResponse({'error': error_msg}, status=400)
                else:
                    messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                    return redirect('payments')
        except ValueError:
            error_msg = "Invalid amount"
            if is_json:
                return JsonResponse({'error': error_msg}, status=400)
            else:
                messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                return redirect('payments')
        
        # Get from account
        try:
            from_account = Account.objects.get(id=from_account_id, customer_profile=profile)
        except Account.DoesNotExist:
            error_msg = "Invalid from account"
            if is_json:
                return JsonResponse({'error': error_msg}, status=400)
            else:
                messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                return redirect('payments')
        
        # Check balance
        if from_account.balance < amount:
            error_msg = "Insufficient funds"
            if is_json:
                return JsonResponse({'error': error_msg}, status=400)
            else:
                messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                return redirect('payments')
        
        recipient = None
        to_account = None
        
        if to_type == 'internal':
            to_account_id = data.get('to_account')
            if not to_account_id:
                error_msg = "To account required for internal transfer"
                if is_json:
                    return JsonResponse({'error': error_msg}, status=400)
                else:
                    messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                    return redirect('payments')
            try:
                to_account = Account.objects.get(id=to_account_id, customer_profile=profile)
            except Account.DoesNotExist:
                error_msg = "Invalid to account"
                if is_json:
                    return JsonResponse({'error': error_msg}, status=400)
                else:
                    messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                    return redirect('payments')
            if from_account.id == to_account.id:
                error_msg = "Cannot transfer to same account"
                if is_json:
                    return JsonResponse({'error': error_msg}, status=400)
                else:
                    messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                    return redirect('payments')
        else:
            # External payment
            recipient_user_id = data.get('recipient_user_id', '').strip().upper()
            if not recipient_user_id:
                error_msg = "Recipient user ID required"
                if is_json:
                    return JsonResponse({'error': error_msg}, status=400)
                else:
                    messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                    return redirect('payments')
            try:
                recipient_profile = CustomerProfile.objects.get(skb_user_id=recipient_user_id)
                recipient, created = Recipient.objects.get_or_create(
                    customer_profile=profile,
                    user_id=recipient_user_id,
                    defaults={'name': f"{recipient_profile.first_name} {recipient_profile.last_name}"}
                )
            except CustomerProfile.DoesNotExist:
                error_msg = "Recipient not found"
                if is_json:
                    return JsonResponse({'error': error_msg}, status=400)
                else:
                    messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                    return redirect('payments')
        
        # Check if scheduled or immediate
        # Parse and validate schedule_date if provided. Accept only YYYY-MM-DD.
        parsed_date = None
        if schedule_date:
            # sanitize common Unicode quotes and whitespace
            sd = schedule_date.strip()
            sd = sd.replace('\u201c', '').replace('\u201d', '').replace('“', '').replace('”', '').strip()
            try:
                parsed_date = datetime.strptime(sd, '%Y-%m-%d').date()
            except Exception:
                error_msg = "Invalid schedule date; must be YYYY-MM-DD"
                if is_json:
                    return JsonResponse({'error': [error_msg]}, status=400)
                else:
                    messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                    return redirect('payments')

        # If recurring is requested, schedule date is required
        if recurring != 'none' and not parsed_date:
            error_msg = "Schedule date required for recurring payments"
            if is_json:
                return JsonResponse({'error': error_msg}, status=400)
            else:
                messages.error(request, f"Dear {request.user.username},\nError message: {error_msg}.")
                return redirect('payments')

        if parsed_date:
            # Scheduled payment
            scheduled_payment = ScheduledPayment.objects.create(
                customer_profile=profile,
                from_account=from_account,
                to_account=to_account,
                recipient=recipient,
                to_type=to_type,
                amount=amount,
                category=category,
                note=note,
                schedule_date=parsed_date,
                recurring=recurring
            )
            if is_json:
                return JsonResponse({
                    'success': True,
                    'message': 'Payment scheduled successfully',
                    'scheduled': True,
                    'id': scheduled_payment.id
                })
            else:
                messages.success(request, f"Dear {request.user.username},\nPayment scheduled successfully.")
                return redirect('payments')
        else:
            # Immediate payment
            payment = Payment.objects.create(
                customer_profile=profile,
                from_account=from_account,
                to_account=to_account,
                recipient=recipient,
                to_type=to_type,
                amount=amount,
                category=category,
                note=note
            )

            # Update balances (convert to decimal where necessary)
            try:
                from_account.balance = from_account.balance - amount
                from_account.save()
            except Exception:
                # fallback: ensure numeric
                from_account.balance -= amount
                from_account.save()

            if to_type == 'internal' and to_account:
                to_account.balance += amount
                to_account.save()
            else:
                # External payment - add money to recipient's savings account
                try:
                    recipient_savings = Account.objects.get(
                        customer_profile=recipient_profile,
                        account_type='savings'
                    )
                    recipient_savings.balance += amount
                    recipient_savings.save()
                except Account.DoesNotExist:
                    # If recipient doesn't have savings account, this shouldn't happen
                    # but let's handle it gracefully
                    pass

            if is_json:
                return JsonResponse({
                    'success': True,
                    'message': 'Payment completed successfully',
                    'scheduled': False,
                    'id': payment.id
                })
            else:
                messages.success(request, f"Dear {request.user.username},\nPayment completed successfully.")
                return redirect('payments')
            
    except CustomerProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def verify_credentials(request):
    """API endpoint to verify user credentials for viewing full account numbers"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        profile = CustomerProfile.objects.get(user=request.user)
        
        data = json.loads(request.body)
        user_id = data.get('user_id', '').strip().upper()
        password = data.get('password', '')
        
        if user_id != profile.skb_user_id:
            return JsonResponse({'error': 'Invalid SKB User ID'}, status=400)
        
        user = authenticate(username=request.user.username, password=password)
        if user is None or user != request.user:
            return JsonResponse({'error': 'Invalid password'}, status=400)
        
        # Return full account numbers
        accounts_data = []
        for account in profile.accounts.all():
            accounts_data.append({
                'id': account.id,
                'type': account.get_account_type_display(),
                'number': account.account_number,
                'balance': float(account.balance)
            })
        
        return JsonResponse({'success': True, 'accounts': accounts_data})
    except CustomerProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)


def get_admin_unread_status(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    customers = CustomerProfile.objects.all()
    unread_customers = {}
    for customer in customers:
        if customer.skb_user_id:
            unread_customers[customer.skb_user_id] = Message.objects.filter(user_id=customer.skb_user_id, sender='user', read=False).exists()
    
    has_any_unread = any(unread_customers.values())
    
    return JsonResponse({
        'has_any_unread': has_any_unread,
        'unread_customers': unread_customers
    })


@login_required
def cancel_scheduled_payment(request):
    """API endpoint to cancel a scheduled payment"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        profile = CustomerProfile.objects.get(user=request.user)
        
        data = json.loads(request.body)
        payment_id = data.get('id')
        
        scheduled_payment = ScheduledPayment.objects.get(id=payment_id, customer_profile=profile)
        
        today = date.today()
        now = datetime.now()
        if scheduled_payment.schedule_date < today or (scheduled_payment.schedule_date == today and now.time() >= time(23, 59)):
            return JsonResponse({'error': 'Cannot cancel past scheduled payment'}, status=400)
        
        scheduled_payment.status = 'Cancelled'
        scheduled_payment.save()
        
        return JsonResponse({'success': True, 'message': 'Scheduled payment cancelled successfully'})
    except ScheduledPayment.DoesNotExist:
        return JsonResponse({'error': 'Scheduled payment not found'}, status=404)
    except CustomerProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    """API endpoint to cancel a scheduled payment"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        profile = CustomerProfile.objects.get(user=request.user)
        
        data = json.loads(request.body)
        payment_id = data.get('id')
        
        scheduled_payment = ScheduledPayment.objects.get(id=payment_id, customer_profile=profile)
        
        today = date.today()
        now = datetime.now()
        if scheduled_payment.status != 'Scheduled':
            return JsonResponse({'error': 'Payment not scheduled'}, status=400)
        
        if scheduled_payment.schedule_date < today or (scheduled_payment.schedule_date == today and now.time() >= time(23, 59)):
            return JsonResponse({'error': 'Cannot cancel past scheduled payment'}, status=400)
        
        scheduled_payment.status = 'Cancelled'
        scheduled_payment.save()
        
        return JsonResponse({'success': True, 'message': 'Scheduled payment cancelled successfully'})
    except ScheduledPayment.DoesNotExist:
        return JsonResponse({'error': 'Scheduled payment not found'}, status=404)
    except CustomerProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    """API endpoint to get user's payments"""
    try:
        profile = CustomerProfile.objects.get(user=request.user)
        payments = profile.payments.all().order_by('-date')[:50]  # Last 50 payments
        scheduled_payments = profile.scheduled_payments.all().order_by('schedule_date')
        
        payments_data = []
        for payment in payments:
            to_display = ""
            if payment.to_type == 'internal':
                to_display = payment.to_account.account_type.title() if payment.to_account else "Unknown"
            else:
                to_display = payment.recipient.name if payment.recipient else "Unknown"
            
            payments_data.append({
                'id': payment.id,
                'date': payment.date.strftime('%Y-%m-%d'),
                'from': payment.from_account.account_type.title(),
                'to': to_display,
                'amount': float(payment.amount),
                'category': payment.category,
                'note': payment.note,
                'status': payment.status
            })
        
        scheduled_data = []
        for sp in scheduled_payments:
            to_display = ""
            if sp.to_type == 'internal':
                to_display = sp.to_account.account_type.title() if sp.to_account else "Unknown"
            else:
                to_display = sp.recipient.name if sp.recipient else "Unknown"
            
            scheduled_data.append({
                'id': sp.id,
                'date': sp.schedule_date.strftime('%Y-%m-%d'),
                'from': sp.from_account.account_type.title(),
                'to': to_display,
                'amount': float(sp.amount),
                'category': sp.category,
                'note': sp.note,
                'status': sp.status,
                'recurring': sp.recurring
            })
        
        return JsonResponse({
            'payments': payments_data,
            'scheduled_payments': scheduled_data
        })
    except CustomerProfile.DoesNotExist:
        return JsonResponse({'error': 'Profile not found'}, status=404)


# @login_required(login_url='login')
def support(request):
    has_unread_admin_message = False
    if request.user.is_authenticated:
        try:
            profile = CustomerProfile.objects.get(user=request.user)
            has_unread_admin_message = Message.objects.filter(user_id=profile.skb_user_id, sender='admin', read=False).exists()
        except CustomerProfile.DoesNotExist:
            pass
    return render(request, 'support.html', {'has_unread_admin_message': has_unread_admin_message})


# @login_required(login_url='login')
def livechat(request):
    if not request.user.is_authenticated:
        return redirect('login')
    profile = CustomerProfile.objects.get(user=request.user)
    return render(request, 'livechat.html', {'user_id': profile.skb_user_id})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            rr = form.save()
            # attach files and save
            id_front = form.cleaned_data.get('id_front')
            id_back = form.cleaned_data.get('id_back')
            if id_front:
                rr.id_front = id_front
            if id_back:
                rr.id_back = id_back
            rr.save()
            # send welcome email to the user (console backend in dev)
            try:
                from django.core.mail import send_mail
                if rr.user and rr.user.email:
                    subject = 'Welcome to Skandia Bank (SKB)'
                    message = f"Hello {rr.user.first_name},\n\nWelcome to Skandia Bank. Your account has been created. Your user id: {rr.skb_user_id}\n\nRegards,\nSKB Team"
                    send_mail(subject, message, None, [rr.user.email])
            except Exception:
                pass
            # create or update CustomerProfile for the created user
            try:
                user = rr.user
                if user:
                    cp, created = CustomerProfile.objects.get_or_create(user=user)
                    cp.first_name = rr.first_name
                    cp.middle_name = rr.middle_name
                    cp.last_name = rr.last_name
                    cp.email = rr.email
                    cp.country_code = rr.country_code
                    cp.phone = rr.phone
                    cp.ssn = rr.ssn
                    cp.approved = rr.approved
                    cp.id_type = rr.id_type
                    if rr.id_front:
                        cp.id_front = rr.id_front
                    if rr.id_back:
                        cp.id_back = rr.id_back
                    cp.skb_user_id = rr.skb_user_id
                    cp.savings_account = rr.savings_account
                    cp.checking_account = rr.checking_account
                    cp.credit_account = rr.credit_account
                    # balances default to 0 on model creation; keep existing otherwise
                    cp.save()
                    # auto-login the newly created user
                    login(request, user)
                    messages.success(request, 'Registration successful — you are now logged in.')
                    # Render a success page that shows the generated SKB id and accounts
                    context = {
                        'skb_user_id': rr.skb_user_id,
                        'savings_account': rr.savings_account,
                        'checking_account': rr.checking_account,
                        'credit_account': rr.credit_account,
                        'savings_balance': getattr(rr, 'savings_balance', 0),
                        'checking_balance': getattr(rr, 'checking_balance', 0),
                        'credit_balance': getattr(rr, 'credit_balance', 0),
                    }
                    return render(request, 'register_success.html', context)
            except Exception:
                pass
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
        else:
            # pass form errors back to template
            return render(request, 'register.html', {'form_errors': form.errors})

    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful')
            next_url = request.GET.get('next') or request.POST.get('next')
            # If next target is a legacy .html file, ignore it and go to named 'home'
            if next_url:
                if '.html' in next_url:
                    return redirect('home')
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
            return render(request, 'login.html')

    return render(request, 'login.html')



def logout_view(request):
    # Check if user is admin before logout
    is_admin = request.user.is_staff or request.user.is_superuser
    # Ensure session is fully cleared and user is logged out
    logout(request)
    try:
        request.session.flush()
    except Exception:
        pass
    messages.info(request, 'Logged out')
    from django.conf import settings
    if is_admin:
        return redirect('admin_login')
    return redirect(getattr(settings, 'LOGOUT_REDIRECT_URL', 'login'))


def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            messages.success(request, 'Admin login successful')
            return redirect('admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not a superuser')
    return render(request, 'admin_login.html')


@login_required(login_url='admin_login')
def admin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied')
        return redirect('admin_login')
    
    # Get total number of registered users
    total_clients = CustomerProfile.objects.count()
    
    # Get superuser's profile and accounts
    try:
        profile = CustomerProfile.objects.get(user=request.user)
        accounts = profile.accounts.all()
        savings_account = accounts.filter(account_type='savings').first()
        checking_account = accounts.filter(account_type='checking').first()
        credit_account = accounts.filter(account_type='credit_card').first()
        
        savings_balance = savings_account.balance if savings_account else 0
        checking_balance = checking_account.balance if checking_account else 0
        credit_balance = credit_account.balance if credit_account else 0
        
        savings_number = savings_account.account_number if savings_account else 'N/A'
        checking_number = checking_account.account_number if checking_account else 'N/A'
        credit_number = '****-****-****-' + credit_account.account_number[-4:] if credit_account and len(credit_account.account_number) >= 4 else (credit_account.account_number if credit_account else 'N/A')
    except CustomerProfile.DoesNotExist:
        # If superuser doesn't have CustomerProfile, set defaults
        savings_balance = 0
        checking_balance = 0
        credit_balance = 0
        savings_number = 'N/A'
        checking_number = 'N/A'
        credit_number = 'N/A'
    
    customers = CustomerProfile.objects.all()
    for customer in customers:
        customer.has_unread = Message.objects.filter(user_id=customer.skb_user_id, sender='user', read=False).exists()
    
    has_any_unread = any(customer.has_unread for customer in customers)
    
    context = {
        'total_clients': total_clients,
        'savings_balance': savings_balance,
        'checking_balance': checking_balance,
        'credit_balance': credit_balance,
        'savings_number': savings_number,
        'checking_number': checking_number,
        'credit_number': credit_number,
        'customers': customers,
        'has_any_unread': has_any_unread,
    }
    return render(request, 'admin_dashboard.html', context)


@login_required(login_url='admin_login')
def admin_livechat(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied')
        return redirect('admin_login')
    return render(request, 'admin_livechat.html', {'user_id': user_id})


@login_required
def send_message(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        message = request.POST.get('message', '')
        file = request.FILES.get('file')
        sender = 'admin' if request.user.is_superuser else 'user'
        
        # For user, check if user_id matches their own
        if not request.user.is_superuser:
            try:
                profile = CustomerProfile.objects.get(user=request.user)
                if profile.skb_user_id != user_id:
                    return JsonResponse({'error': 'Unauthorized'}, status=403)
            except CustomerProfile.DoesNotExist:
                return JsonResponse({'error': 'Profile not found'}, status=404)
        
        from userprofile.models import Message
        msg = Message.objects.create(
            user_id=user_id,
            sender=sender,
            message=message,
            file=file
        )
        return JsonResponse({'status': 'ok', 'id': msg.id})
    return JsonResponse({'error': 'Invalid method'}, status=405)


@login_required
def get_messages(request, user_id):
    # For user, check if user_id matches their own
    if not request.user.is_superuser:
        try:
            profile = CustomerProfile.objects.get(user=request.user)
            if profile.skb_user_id != user_id:
                return JsonResponse({'error': 'Unauthorized'}, status=403)
        except CustomerProfile.DoesNotExist:
            return JsonResponse({'error': 'Profile not found'}, status=404)
    
    from userprofile.models import Message
    messages = Message.objects.filter(user_id=user_id).order_by('timestamp')
    data = []
    for m in messages:
        item = {
            'id': m.id,
            'sender': m.sender,
            'message': m.message,
            'timestamp': m.timestamp.isoformat(),
            'file_url': m.file.url if m.file else None,
            'file_name': m.file.name.split('/')[-1] if m.file else None
        }
        data.append(item)
    return JsonResponse({'messages': data})
 

def register_pdf(request):
    """Return a simple PDF summary for the logged-in user's CustomerProfile.

    Uses ReportLab if available; otherwise returns a plain text response explaining
    the missing dependency.
    """
    if not request.user.is_authenticated:
        return redirect('login')
    cp = get_object_or_404(CustomerProfile, user=request.user)
    if not REPORTLAB_AVAILABLE:
        return HttpResponse("PDF generation library not installed. Install reportlab to enable PDF downloads.")

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    x = 72
    y = 720
    p.setFont("Helvetica-Bold", 16)
    p.drawString(x, y, "Skandia Bank (SKB) — Account Summary")
    y -= 30
    p.setFont("Helvetica", 12)
    p.drawString(x, y, f"User: {request.user.username}")
    y -= 18
    p.drawString(x, y, f"SKB User ID: {cp.skb_user_id}")
    y -= 18
    p.drawString(x, y, f"Name: {cp.first_name} {cp.middle_name} {cp.last_name}".strip())
    y -= 18
    p.drawString(x, y, f"Email: {cp.email}")
    y -= 24
    p.setFont("Helvetica-Bold", 13)
    p.drawString(x, y, "Accounts")
    y -= 18
    p.setFont("Helvetica", 12)
    # Fetch related Account objects (accounts created via post_save)
    try:
        savings = cp.accounts.filter(account_type='savings').first()
        checking = cp.accounts.filter(account_type='checking').first()
        credit = cp.accounts.filter(account_type='credit_card').first()
    except Exception:
        savings = checking = credit = None

    s_acc = savings.account_number if savings and getattr(savings, 'account_number', None) else 'N/A'
    s_bal = f"{savings.balance:.2f}" if savings and getattr(savings, 'balance', None) is not None else "0.00"
    p.drawString(x, y, f"Savings: {s_acc} — Balance: ${s_bal}")
    y -= 16

    c_acc = checking.account_number if checking and getattr(checking, 'account_number', None) else 'N/A'
    c_bal = f"{checking.balance:.2f}" if checking and getattr(checking, 'balance', None) is not None else "0.00"
    p.drawString(x, y, f"Checking: {c_acc} — Balance: ${c_bal}")
    y -= 16

    cr_acc = credit.account_number if credit and getattr(credit, 'account_number', None) else 'N/A'
    cr_bal = f"{credit.balance:.2f}" if credit and getattr(credit, 'balance', None) is not None else "0.00"
    p.drawString(x, y, f"Credit: {cr_acc} — Balance: ${cr_bal}")
    y -= 24
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(x, y, f"Created: {cp.created_at}")

    p.showPage()
    p.save()
    buffer.seek(0)
    resp = HttpResponse(buffer.read(), content_type='application/pdf')
    resp['Content-Disposition'] = 'attachment; filename="skb_account_summary.pdf"'
    return resp