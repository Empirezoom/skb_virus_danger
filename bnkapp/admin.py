from django.contrib import admin
from . models import *

# Register your models here.


class SkBankAdmin(admin.ModelAdmin):
    list_display = ['id','name','email','address']
    prepopulated_fields = {'slug':('name',)}



admin.site.register(SkBank, SkBankAdmin)