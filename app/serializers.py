from rest_framework import serializers
from .models import *

class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = '__all__'

class ShipmentSerializer(serializers.ModelSerializer):
    parts = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    moderator = serializers.SerializerMethodField()

    def get_parts(self, shipment):
        # Получаем все связи между частями и отправками
        part_shipments = PartShipment.objects.filter(shipment=shipment)
        parts = [part_shipment.part for part_shipment in part_shipments]  # Извлекаем детали
        serializer = PartSerializer(parts, many=True)
        return serializer.data
    
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

