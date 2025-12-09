# from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Stock, Subscription

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name')
    search_fields = ('ticker', 'name')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'created_at')
    list_filter = ('stock',)

