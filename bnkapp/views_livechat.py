from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Message, BalanceRequest, WithdrawalRequest, PaymentDetail, OTPLog

@login_required
@require_POST
def send_message(request):
    user_id = request.POST.get("user_id")
    msg = request.POST.get("message", "").strip()
    f = request.FILES.get("file")
    sender = "admin" if request.user.is_staff else "user"
    m = Message.objects.create(user_id=user_id, sender=sender, message=msg, file=f, timestamp=timezone.now())
    return JsonResponse({"status": "ok", "message_id": m.id})

@login_required
def get_messages(request, user_id):
    qs = Message.objects.filter(user_id=user_id).order_by("timestamp")
    msgs = [m.to_dict() for m in qs]
    # Mark messages as read based on who is viewing
    if request.user.is_staff:
        # Admin viewing: mark user messages as read
        Message.objects.filter(user_id=user_id, sender='user', read=False).update(read=True)
    else:
        # User viewing: mark admin messages as read
        Message.objects.filter(user_id=user_id, sender='admin', read=False).update(read=True)
    return JsonResponse({"status": "ok", "messages": msgs})

@login_required
def get_pending_withdrawal_otp(request, user_id):
    if not request.user.is_staff:
        return JsonResponse({"status": "error", "error": "Unauthorized"}, status=403)
    wr = WithdrawalRequest.objects.filter(user_id=user_id, status='pending').first()
    if wr:
        return JsonResponse({"status": "ok", "otp": wr.otp})
    return JsonResponse({"status": "ok", "otp": None})

@login_required
@require_POST
def add_balance(request):
    user_id = request.POST.get("user_id")
    account_name = request.POST.get("account_name", "")
    mode = request.POST.get("mode", "")
    amount = request.POST.get("amount", "0")
    try:
        br = BalanceRequest.objects.create(user_id=user_id, account_name=account_name, mode=mode, amount=amount)
        Message.objects.create(user_id=user_id, sender="user", message=f"Add Balance Request: {account_name} | {mode} | ${amount}")
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=400)

@login_required
@require_POST
def withdraw(request):
    user_id = request.POST.get("user_id")
    otp = request.POST.get("otp", "")
    try:
        # Find the pending withdrawal for this user
        wr = WithdrawalRequest.objects.filter(user_id=user_id, status='pending').first()
        if not wr:
            return JsonResponse({"status": "error", "error": "No pending withdrawal found."}, status=400)
        if wr.otp != otp:
            return JsonResponse({"status": "error", "error": "Incorrect OTP."}, status=400)
        wr.status = 'completed'
        wr.save()
        Message.objects.create(user_id=user_id, sender="user", message=f"Withdrawal Request:\nBank: {wr.bank}\nAccount: {wr.account}\nAccountName: {wr.routing}\nAmount: ${wr.amount}\n\nWithdrawal info submitted. Please wait for admin approval.")
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=400)

@login_required
@require_POST
def send_payment(request):
    user_id = request.POST.get("user_id")
    mode = request.POST.get("mode", "")
    account = request.POST.get("account", "")
    transaction_id = request.POST.get("transaction_id", "")
    try:
        PaymentDetail.objects.create(user_id=user_id, mode=mode, account=account, transaction_id=transaction_id)
        Message.objects.create(user_id=user_id, sender="admin", message=f"Payment Details: {mode} | {account} | REF:{transaction_id}")
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=400)

@login_required
@require_POST
def send_otp(request):
    user_id = request.POST.get("user_id")
    otp = request.POST.get("otp", "")
    try:
        OTPLog.objects.create(user_id=user_id, otp=otp)
        Message.objects.create(user_id=user_id, sender="admin", message=f"OTP: {otp}")
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=400)

@login_required
@require_POST
def generate_withdrawal_otp(request):
    user_id = request.POST.get("user_id")
    bank = request.POST.get("bank", "")
    account = request.POST.get("account", "")
    routing = request.POST.get("routing", "")
    amount = request.POST.get("amount", "0")
    import random
    def generate_valid_otp():
        while True:
            otp = str(random.randint(100000000, 999999999))
            digits = [int(d) for d in otp]
            # Check if all digits are the same
            if len(set(digits)) == 1:
                continue
            # Check if sequential ascending
            if digits == list(range(digits[0], digits[0] + 9)):
                continue
            # Check if sequential descending
            if digits == list(range(digits[0], digits[0] - 9, -1)):
                continue
            # Check if already used by this user
            if WithdrawalRequest.objects.filter(user_id=user_id, otp=otp).exists():
                continue
            return otp
    otp = generate_valid_otp()
    try:
        wr = WithdrawalRequest.objects.create(user_id=user_id, bank=bank, account=account, routing=routing, amount=amount, otp=otp, status='pending')
        return JsonResponse({"status": "ok", "withdrawal_id": wr.id})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)}, status=400)