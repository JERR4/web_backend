from rest_framework import serializers
from .models import *
from django.db.models import Sum

class PartSerializer(serializers.ModelSerializer):
    active_add = serializers.SerializerMethodField()

    def get_active_add(self, part):
        has_shipment = PartShipment.objects.filter(part=part, shipment__status=1).exists()
        return not has_shipment

    class Meta:
        model = Part
        fields = '__all__'

class CreateUpdatePartSerializer(serializers.ModelSerializer):
    active_add = serializers.SerializerMethodField()

    def get_active_add(self, part):
        has_shipment = PartShipment.objects.filter(part=part, shipment__status=1).exists()
        return not has_shipment

    class Meta:
        model = Part
        exclude = ['image']

class ShipmentSerializer(serializers.ModelSerializer):
    parts_amount = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    moderator = serializers.SerializerMethodField()

    def get_parts_amount(self, shipment):
        return PartShipment.objects.filter(shipment=shipment).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    def get_owner(self, shipment):
        return shipment.owner.username

    def get_moderator(self, shipment):
        if shipment.moderator:
            return shipment.moderator.username
        return None

    class Meta:
        model = Shipment
        fields = '__all__'

class PartShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartShipment
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'username')
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
        )
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        if "password" in validated_data:
            instance.set_password(validated_data["password"])
        instance.save()
        return instance
