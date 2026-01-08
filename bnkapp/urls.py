from django.urls import path
from . import views
from . import views_livechat

urlpatterns = [
    path('', views.home, name='home'),
    path('account/', views.account, name='account'),
    path('payments/', views.payments, name='payments'),
    path('support/', views.support, name='support'),
    path('livechat/', views.livechat, name='livechat'),
    path('register/', views.register, name='register'),
    path('register/pdf/', views.register_pdf, name='register_pdf'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-livechat/<str:user_id>/', views.admin_livechat, name='admin_livechat'),
    path("send_message/", views_livechat.send_message, name="send_message"),
    path("get_messages/<str:user_id>/", views_livechat.get_messages, name="get_messages"),
    path("get_pending_withdrawal_otp/<str:user_id>/", views_livechat.get_pending_withdrawal_otp, name="get_pending_withdrawal_otp"),
    path("add_balance/", views_livechat.add_balance, name="add_balance"),
    path("withdraw/", views_livechat.withdraw, name="withdraw"),
    path("generate_withdrawal_otp/", views_livechat.generate_withdrawal_otp, name="generate_withdrawal_otp"),
    path("send_payment/", views_livechat.send_payment, name="send_payment"),
    path("send_otp/", views_livechat.send_otp, name="send_otp"),
    # API endpoints
    path('api/accounts/', views.get_accounts, name='api_accounts'),
    path('api/recipient/lookup/', views.lookup_recipient, name='api_lookup_recipient'),
    path('api/recipient/save/', views.save_recipient, name='api_save_recipient'),
    path('api/payment/create/', views.create_payment, name='api_create_payment'),
    path('api/scheduled-payment/cancel/', views.cancel_scheduled_payment, name='api_cancel_scheduled_payment'),
    path('api/verify-credentials/', views.verify_credentials, name='api_verify_credentials'),
    path('api/admin/unread-status/', views.get_admin_unread_status, name='api_admin_unread_status'),
]
