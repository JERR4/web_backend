from django.contrib import admin
from .models import Part, Shipment, PartShipment

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('part_name', 'specification', 'oem_number', 'status', 'image', 'short_description', 'dimensions', 'weight')
    search_fields = ('part_name', 'oem_number', 'specification')
    list_filter = ('status',)
    ordering = ('part_name',)

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'creation_date', 'formation_date', 'completion_date', 'owner', 'moderator', 'operation_type')
    search_fields = ('id', 'owner__username', 'moderator__username')
    list_filter = ('status', 'operation_type')
    ordering = ('-creation_date',)

@admin.register(PartShipment)
class PartShipmentAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'part', 'quantity')
    search_fields = ('shipment__id', 'part__part_name')
    list_filter = ('shipment', 'part')
    ordering = ('shipment', 'part')