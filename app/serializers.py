from rest_framework import serializers
from .models import *
from django.db.models import Sum


class PartSerializer(serializers.ModelSerializer):
    active_add = serializers.SerializerMethodField()

    def get_active_add(self, part) -> bool:
        user = self.context.get('user')
        if not user:
            return False
        
        has_shipment = PartShipment.objects.filter(part=part, shipment__status=1, shipment__owner_id=user.id).exists()
        return not has_shipment

    
    class Meta:
        model = Part
        fields = '__all__'
        extra_kwargs = {
            "id": {"read_only": True, "required": True},
            "active_add": {"type": "boolean", "help_text": "Indicates whether the part is active or not."},
        }


class PartialPartSerializer(serializers.ModelSerializer):
    quantity = serializers.SerializerMethodField()

    def get_quantity(self, part) -> int:
        user = self.context.get('user')
        print(f"Полученный пользователь: {user}")  # Проверяем пользователя

        if not user:
            print("Пользователь отсутствует")
            return 0

        # Выполняем запрос для PartShipment
        part_shipments = PartShipment.objects.filter(
            part=part, 
            shipment__owner_id=user.id
        )
        print(f"Запрос PartShipment: {part_shipments.query}")
        part_shipment = part_shipments.first()

        if part_shipment:
            print(f"Найден PartShipment: {part_shipment}")
            return part_shipment.quantity
        else:
            print("PartShipment не найден или quantity равно None")
            return 0

    class Meta:
        model = Part
        fields = ('id', 'part_name', 'specification', 'oem_number', 'image', 'quantity')


class CreateUpdatePartSerializer(serializers.ModelSerializer):
    active_add = serializers.SerializerMethodField()

    def get_active_add(self, part) -> bool:
        has_shipment = PartShipment.objects.filter(part=part, shipment__status=1).exists()
        return not has_shipment

    class Meta:
        model = Part
        exclude = ['image']

    @property
    def swagger_schema_fields(self):
        return {
            "active_add": {
                "type": "boolean",
                "description": "Indicates whether the part is active or not.",
            },
        }


class ShipmentsSerializer(serializers.ModelSerializer):
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

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

class OneShipmentSerializer(serializers.ModelSerializer):
    parts_amount = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    parts = serializers.SerializerMethodField()
    moderator = serializers.SerializerMethodField()

    def get_parts_amount(self, shipment):
        return PartShipment.objects.filter(shipment=shipment).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    def get_owner(self, shipment):
        return shipment.owner.username

    def get_parts(self, shipment):
        user = self.context.get('user')
        parts = shipment.get_parts()
        return PartialPartSerializer(parts, many=True, context={"user": user}).data

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
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
        )
        print("User created successfully:", user)
        return user

    def update(self, instance, validated_data):
            print("Received validated data:", validated_data)

            if 'email' in validated_data:
                instance.email = validated_data['email']
            if 'first_name' in validated_data:
                instance.first_name = validated_data['first_name']
            if 'last_name' in validated_data:
                instance.last_name = validated_data['last_name']
            if 'password' in validated_data:
                print("Password from validated_data:", validated_data['password'])
                instance.set_password(validated_data['password'])
            if 'username' in validated_data:
                instance.username = validated_data['username']

            instance.save()
            print("Instance saved successfully with updated data")
            return instance

