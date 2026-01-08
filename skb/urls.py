"""
URL configuration for skb project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from bnkapp import views as bnk_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('skb-empire/', admin.site.urls),
    path('', include('bnkapp.urls')),
    # Ensure /accounts/logout/ uses our app logout view (accepts GET/POST)
    path('accounts/logout/', bnk_views.logout_view, name='accounts_logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]


if settings.DEBUG:
    # Serve static files from STATICFILES_DIRS in development (useful when STATIC_ROOT is empty)
    if getattr(settings, 'STATICFILES_DIRS', None):
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    else:
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)