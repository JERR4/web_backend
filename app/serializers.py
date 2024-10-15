from rest_framework import serializers
from .models import *

class PartSerializer(serializers.ModelSerializer):
    active_add = serializers.SerializerMethodField()

    def get_active_add(self, part):
        has_shipment = PartShipment.objects.filter(part=part, shipment__status=1).exists()
        return not has_shipment

    class Meta:
        model = Part
        fields = '__all__'

class ShipmentSerializer(serializers.ModelSerializer):
    parts_amount = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    moderator = serializers.SerializerMethodField()

    def get_parts_amount(self,shipment):
        return PartShipment.objects.filter(shipment=shipment).count()
    def get_owner(self, shipment):
        return shipment.owner.username

    def get_moderator(self, shipment):
        if shipment.moderator:
            return shipment.moderator.username
        return None  # Возвращаем None, если модератора нет

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
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'date_joined', 'password', 'username')


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'first_name', 'last_name', 'username')
        write_only_fields = ('password',)
        read_only_fields = ('id',)

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

