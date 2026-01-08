from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from userprofile.models import CustomerProfile, Account, Transaction


class PaymentTests(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(username='alice', password='pass')
		self.user2 = User.objects.create_user(username='bob', password='pass')

		# Create customer profiles
		self.cp1 = CustomerProfile.objects.create(user=self.user, first_name='Alice', last_name='A', email='a@example.com')
		self.cp2 = CustomerProfile.objects.create(user=self.user2, first_name='Bob', last_name='B', email='b@example.com')

		# Ensure accounts exist and set balances
		self.from_account = self.cp1.accounts.get(account_type='checking')
		self.to_account = self.cp1.accounts.get(account_type='savings')
		self.from_account.balance = 1000.00
		self.from_account.save()
		self.to_account.balance = 100.00
		self.to_account.save()

		# Recipient (bob) savings
		self.bob_savings = self.cp2.accounts.get(account_type='savings')
		self.bob_savings.balance = 50.00
		self.bob_savings.save()

		self.client = Client()
		self.client.login(username='alice', password='pass')

	def test_internal_transfer_creates_transactions_and_updates_balances(self):
        url = reverse('payments')
        data = {
            'from_account': str(self.from_account.id),
            'to_type': 'internal',
            'to_account_internal': str(self.to_account.id),
            'amount': '100.00',
            'category': 'General',
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)  # redirect after success
		self.to_account.refresh_from_db()
		self.assertEqual(float(self.from_account.balance), 900.00)
		self.assertEqual(float(self.to_account.balance), 200.00)
		# Check transactions
		txs_from = Transaction.objects.filter(account=self.from_account)
		txs_to = Transaction.objects.filter(account=self.to_account)
		self.assertTrue(txs_from.exists())
		self.assertTrue(txs_to.exists())

	def test_external_payment_credits_recipient_savings(self):
        url = reverse('payments')
        # set recipient skb_user_id for bob
        self.cp2.skb_user_id = 'SKB-TEST-BOB'
        self.cp2.save()

        data = {
            'from_account': str(self.from_account.id),
            'to_type': 'external',
            'recipient_user_id': 'SKB-TEST-BOB',
            'amount': '25.00',
            'category': 'General',
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)  # redirect after success
		self.bob_savings.refresh_from_db()
		self.assertEqual(float(self.from_account.balance), 875.00)
		self.assertEqual(float(self.bob_savings.balance), 75.00)
		self.assertTrue(Transaction.objects.filter(account=self.bob_savings).exists())
