from django.contrib import admin
from .models import Part, Order, PartOrder

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('part_name', 'specification', 'oem_number', 'status', 'image', 'short_description', 'dimensions', 'weight')
    search_fields = ('part_name', 'oem_number', 'specification')
    list_filter = ('status',)
    ordering = ('part_name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'creation_date', 'formation_date', 'completion_date', 'owner', 'moderator', 'operation_type')
    search_fields = ('id', 'owner__username', 'moderator__username')
    list_filter = ('status', 'operation_type')
    ordering = ('-creation_date',)

@admin.register(PartOrder)
class PartOrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'part', 'quantity')
    search_fields = ('order__id', 'part__part_name')
    list_filter = ('order', 'part')
    ordering = ('order', 'part')