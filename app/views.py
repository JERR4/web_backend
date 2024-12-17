from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import *
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view
from django.utils import timezone
from django.contrib.auth import authenticate
from .minio import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
    parser_classes,
)
from rest_framework.permissions import AllowAny
from .authorization import *
from .redis import session_storage
from .utils import *
from rest_framework.parsers import FormParser
import uuid

@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            "part_name",
            openapi.IN_QUERY,
            description="Фильтрация по частичному совпадению имени детали",
            type=openapi.TYPE_STRING,
        ),
    ],
    responses={
        status.HTTP_200_OK: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "parts": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_OBJECT),
                    description="Список найденных деталей",
                ),
                "draft_shipment_id": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="ID черновика отправки, если существует",
                    nullable=True,
                ),
                "parts_amount": openapi.Schema(
                    type=openapi.TYPE_NUMBER,
                    description="Количество деталей в отправке, если существует",
                    nullable=True,
                ),
            },
        ),
        status.HTTP_400_BAD_REQUEST: "Неверный запрос",
        status.HTTP_403_FORBIDDEN: "Доступ запрещен",
    },
)

# GET список. В списке услуг возвращается id заявки-черновика этого пользователя для страницы заявки в статусе черновик

@api_view(["GET"])
@permission_classes([AllowAny])
@authentication_classes([AuthBySessionIDIfExists])
def get_parts_list(request):
    part_name = request.GET.get("part_name", "")
    
    parts = Part.objects.filter(status=True, part_name__icontains=part_name).order_by('id')
    serializer = PartSerializer(parts, many=True, context={"user": request.user})
    
    draft_shipment = None
    parts_amount = None
    if request.user:
        try:
            draft_shipment = Shipment.objects.get(status=1, owner=request.user)
            parts_amount = PartShipment.objects.filter(shipment=draft_shipment).count()
        except Shipment.DoesNotExist:
            draft_shipment = None
    
    response = {
        "parts": serializer.data,
        "draft_shipment_id": draft_shipment.pk if draft_shipment else None,
        "parts_amount": parts_amount
    }

    return Response(response, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method="get",
    responses={
        status.HTTP_200_OK: PartSerializer(),
        status.HTTP_404_NOT_FOUND: "Деталь не найдена",
    },
)

# GET одна запись
@api_view(["GET"])
@permission_classes([AllowAny])
def get_part_by_id(request, part_id):
    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return Response({"Ошибка": "Деталь не найдена"}, status=status.HTTP_404_NOT_FOUND)

    serializer = PartSerializer(part, many=False)

    return Response(serializer.data)

@swagger_auto_schema(
    method="post",
    request_body=CreateUpdatePartSerializer,
    responses={
        status.HTTP_201_CREATED: PartSerializer(),
        status.HTTP_400_BAD_REQUEST: "Неверные данные",
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему как модератор",
    },
)

# POST добавление
@api_view(["POST"])
@permission_classes([IsManagerAuth])
def create_part(request):
    part_data = request.data.copy()
    part_data.pop('image', None)
    
    serializer = CreateUpdatePartSerializer(data=part_data)
    serializer.is_valid(raise_exception=True)
    new_part = serializer.save()
    return Response(PartSerializer(new_part).data, status=status.HTTP_201_CREATED)

@swagger_auto_schema(
    method="put",
    request_body=CreateUpdatePartSerializer,
    responses={
        status.HTTP_200_OK: PartSerializer(),
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему как модератор",
        status.HTTP_404_NOT_FOUND: "Деталь не найдена",
        status.HTTP_400_BAD_REQUEST: "Неверные данные",
    },
)

@api_view(["PUT"])
@permission_classes([IsManagerAuth])
def update_part(request, part_id):
    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return Response({"Ошибка": "Деталь не найдена"}, status=status.HTTP_404_NOT_FOUND)

    part_data = request.data.copy()
    part_data.pop('image', None) 

    serializer = CreateUpdatePartSerializer(part, data=part_data, partial=True)
    serializer.is_valid(raise_exception=True)
    updated_part = serializer.save()

    return Response(PartSerializer(updated_part).data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method="delete",
    responses={
        status.HTTP_200_OK: PartSerializer(many=True),
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему как модератор",
        status.HTTP_404_NOT_FOUND: "Деталь не найдена",
    },
)

# DELETE удаление. Удаление изображения встроено в метод удаления услуги
@api_view(["DELETE"])
@permission_classes([IsManagerAuth])
def delete_part(request, part_id):
    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return Response({"Ошибка": "Деталь не найдена"}, status=status.HTTP_404_NOT_FOUND)

    part.status = False
    part.save()

    parts = Part.objects.filter(status=1)
    serializer = PartSerializer(parts, many=True)
    return Response(serializer.data)

@swagger_auto_schema(
    method="post",
    responses={
        status.HTTP_201_CREATED: ShipmentsSerializer(),
        status.HTTP_404_NOT_FOUND: "Деталь не найдена",
        status.HTTP_400_BAD_REQUEST: "Деталь уже добавлена в черновик",
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "Ошибка при создании связки",
    },
)

#POST добавления в заявку-черновик. Заявка создается пустой, указывается автоматически создатель, дата создания и статус, 
# остальные поля указываются через PUT или смену статуса

@api_view(["POST"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def add_part_to_shipment(request, part_id):
    print(f"Received request to add part with ID: {part_id}")
    
    try:
        # Попытка получить деталь
        part = Part.objects.get(pk=part_id)
        print(f"Found part: {part}")
    except Part.DoesNotExist:
        print(f"Part with ID {part_id} does not exist.")
        return Response({"error": "Деталь не найдена"}, status=status.HTTP_404_NOT_FOUND)

    print(f"Looking for or creating draft shipment for user: {request.user}")
    draft_shipment, created = Shipment.objects.get_or_create(
        status=1,
        owner=request.user,
        defaults={'creation_date': timezone.now()}
    )
    if created:
        print("Created new draft shipment.")
    else:
        print("Found existing draft shipment.")

    # Проверяем, существует ли уже связь
    if PartShipment.objects.filter(shipment=draft_shipment, part=part).exists():
        print("Part is already added to the draft shipment.")
        return Response({"error": "Деталь уже добавлена в черновик"}, status=status.HTTP_400_BAD_REQUEST)

    print("Attempting to create PartShipment entry.")
    try:
        PartShipment.objects.create(
            shipment=draft_shipment,
            part=part
        )
        print("PartShipment created successfully.")
    except Exception as e:
        print(f"Exception occurred while creating PartShipment: {str(e)}")
        return Response({"error": f"Ошибка при создании связки: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Сериализация данных
    serializer = ShipmentsSerializer(draft_shipment)
    print("Returning serialized data.")
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@swagger_auto_schema(
    method="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "image": openapi.Schema(type=openapi.TYPE_FILE, description="Новое изображение для детали"),
        },
        required=["image"]
    ),
    responses={
        status.HTTP_200_OK: PartSerializer(),
        status.HTTP_400_BAD_REQUEST: "Изображение не предоставлено",
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему как модератор",
        status.HTTP_404_NOT_FOUND: "Деталь не найдена",
    },
)

# POST добавление изображения. Добавление изображения по id услуги, старое изображение заменяется/удаляется
@api_view(["POST"])
@permission_classes([IsManagerAuth])
def update_part_image(request, part_id):
    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return Response({"Ошибка": "Деталь не найдена"}, status=status.HTTP_404_NOT_FOUND)

    image = request.FILES.get("image")
    
    if image is not None:
        pic_result = add_pic(part, image)
        if 'error' in pic_result.data:
            return pic_result 
        
        serializer = PartSerializer(part)
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response({"Ошибка": "Изображение не предоставлено"}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method="get",
    manual_parameters=[
        openapi.Parameter(
            name="status",
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_INTEGER,
            description="Фильтр по статусу отправки",
        ),
        openapi.Parameter(
            name="date_formation_start",
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Начальная дата формирования (формат: YYYY-MM-DDTHH:MM:SS)",
        ),
        openapi.Parameter(
            name="date_formation_end",
            in_=openapi.IN_QUERY,
            type=openapi.TYPE_STRING,
            format=openapi.FORMAT_DATETIME,
            description="Конечная дата формирования (формат: YYYY-MM-DDTHH:MM:SS)",
        ),
    ],
    responses={
        status.HTTP_200_OK: ShipmentsSerializer(many=True),
        status.HTTP_400_BAD_REQUEST: "Некорректный запрос",
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему",
    },
)

# GET список (кроме удаленных и черновика, модератор и создатель через логины)
@api_view(["GET"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def get_shipments_list(request):
    status = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    shipments = Shipment.objects.exclude(status__in=[1, 2])
    if not request.user.is_superuser:
        shipments = shipments.filter(owner=request.user)
    if status > 0:
        shipments = shipments.filter(status=status)

    if date_formation_start and parse_datetime(date_formation_start):
        shipments = shipments.filter(formation_date__gte=parse_datetime(date_formation_start))

    if date_formation_end and parse_datetime(date_formation_end):
        shipments = shipments.filter(formation_date__lt=parse_datetime(date_formation_end))

    serializer = ShipmentsSerializer(shipments, many=True)

    return Response(serializer.data)

@swagger_auto_schema(
    method="get",
responses={
    status.HTTP_200_OK: openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "id": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                title="ID",
                readOnly=True,
            ),
            "parts_amount": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                title="Parts amount",
                readOnly=True,
            ),
            "owner": openapi.Schema(
                type=openapi.TYPE_STRING,
                title="Owner",
                readOnly=True,
            ),
            "parts": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                title="Parts",
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "part_name": openapi.Schema(type=openapi.TYPE_STRING),
                        "specification": openapi.Schema(type=openapi.TYPE_STRING),
                        "oem_number": openapi.Schema(type=openapi.TYPE_STRING),
                        "image": openapi.Schema(type=openapi.TYPE_STRING, format="uri"),
                    },
                ),
                readOnly=True,
            ),
            "moderator": openapi.Schema(
                type=openapi.TYPE_STRING,
                title="Moderator",
                readOnly=True,
                nullable=True,
            ),
            "status": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                title="Статус",
                enum=[1, 2, 3, 4, 5],
            ),
            "creation_date": openapi.Schema(
                type=openapi.TYPE_STRING,
                format="date-time",
                title="Дата создания",
            ),
            "formation_date": openapi.Schema(
                type=openapi.TYPE_STRING,
                format="date-time",
                title="Дата формирования",
                nullable=True,
            ),
            "planned_date": openapi.Schema(
                type=openapi.TYPE_STRING,
                format="date",
                title="Дата запланированного завершения",
                nullable=True,
            ),
            "completion_date": openapi.Schema(
                type=openapi.TYPE_STRING,
                format="date-time",
                title="Дата завершения",
                nullable=True,
            ),
            "storage": openapi.Schema(
                type=openapi.TYPE_STRING,
                title="Название склада",
                maxLength=50,
                nullable=True,
            ),
            "operation_type": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                title="Тип операции",
                nullable=True,
                enum=[True, False],
            ),
            "license_plate_number": openapi.Schema(
                type=openapi.TYPE_STRING,
                title="Номер автомобиля",
                maxLength=10,
                nullable=True,
            ),
        },
    ),
    status.HTTP_403_FORBIDDEN: "Вы не вошли в систему",
    status.HTTP_404_NOT_FOUND: "Отправка не найдена",
}
)

# GET одна запись (поля заявки + ее услуги). При получении заявки возвращается список ее услуг с картинками
@api_view(["GET"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def get_shipment_by_id(request, shipment_id):

    try:
        shipment = Shipment.objects.get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return Response({"Ошибка": "Отправка не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_superuser and shipment.owner != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)

    serializer = OneShipmentSerializer(shipment, many=False, context={"user": shipment.owner})
    return Response(serializer.data)

@swagger_auto_schema(
    method="put",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "planned_date": openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATETIME,
                description="Запланированная дата отправки (формат: YYYY-MM-DDTHH:MM:SS)",
            ),
            "storage": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Название склада, с которого будет произведена отправка",
            ),
            "operation_type": openapi.Schema(
                type=openapi.TYPE_BOOLEAN,
                description="Тип отправки (доставка/отгрузка)",
            ),
        },
    ),
    responses={
        status.HTTP_200_OK: ShipmentsSerializer(),
        status.HTTP_400_BAD_REQUEST: "Нет данных для обновления или поля не разрешены",
        status.HTTP_403_FORBIDDEN: "Доступ запрещен",
        status.HTTP_404_NOT_FOUND: "Отправка не найдена",
    },
)

# PUT изменение доп. полей заявки
@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def update_shipment(request, shipment_id):
    try:
        shipment = Shipment.objects.get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return Response({"Ошибка": "Отправка не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_superuser and shipment.owner != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    allowed_fields = ['planned_date', 'storage', 'operation_type']

    data = {key: value for key, value in request.data.items() if key in allowed_fields}

    if not data:
        return Response({"Ошибка": "Нет данных для обновления или поля не разрешены"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ShipmentsSerializer(shipment, data=data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method="put",
    responses={
        status.HTTP_200_OK: ShipmentsSerializer(),
        status.HTTP_400_BAD_REQUEST: "Не заполнены обязательные поля: [поля, которые не заполнены]",
        status.HTTP_403_FORBIDDEN: "Доступ запрещен",
        status.HTTP_404_NOT_FOUND: "Отправка не найдена",
        status.HTTP_405_METHOD_NOT_ALLOWED: "Отправка не в статусе 'Черновик'",
    },
)

# PUT сформировать создателем. Происходит проверка на обязательные поля
@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def update_status_user(request, shipment_id):
    try:
        shipment = Shipment.objects.get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return Response({"Ошибка": "Отправка не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_superuser and shipment.owner != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    if shipment.status != 1:
        return Response({"Ошибка": "Отправку нельзя изменить, так как она не в статусе 'Черновик'"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    required_fields = ['planned_date', 'storage', 'operation_type']

    missing_fields = [field for field in required_fields if not getattr(shipment, field)]

    if missing_fields:
        return Response(
            {"Ошибка": f"Не заполнены обязательные поля: {', '.join(missing_fields)}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    shipment.status = 3
    shipment.formation_date = timezone.now()
    shipment.save()

    serializer = ShipmentsSerializer(shipment, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method="put",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "status": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="Новый статус отправки (4 для завершения, 5 для отклонения)",
            ),
        },
        required=["status"],
    ),
    responses={
        status.HTTP_200_OK: ShipmentsSerializer(),
        status.HTTP_403_FORBIDDEN: "Вы не вошли в систему как модератор",
        status.HTTP_404_NOT_FOUND: "Отправка не найдена",
        status.HTTP_405_METHOD_NOT_ALLOWED: "Отправка не статусе 'Сформирована'",
    },
)

# PUT завершить/отклонить модератором
@api_view(["PUT"])
@permission_classes([IsManagerAuth])
@authentication_classes([AuthBySessionID])
def update_status_admin(request, shipment_id):
    try:
        shipment = Shipment.objects.get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return Response({"Ошибка": "Отправка не найдена"}, status=status.HTTP_404_NOT_FOUND)

    request_status = int(request.data["status"])

    if request_status not in [4, 5]:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if shipment.status != 3:
        return Response({"Ошибка": "Отправка не статусе 'Сформирована'"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    shipment.completion_date = timezone.now()
    shipment.status = request_status
    shipment.moderator = request.user
    shipment.license_plate_number = rand_number()
    shipment.save()

    serializer = ShipmentsSerializer(shipment, many=False)

    return Response(serializer.data)

@swagger_auto_schema(
    method="delete",
    responses={
        status.HTTP_200_OK: ShipmentsSerializer(),
        status.HTTP_403_FORBIDDEN: "Доступ запрещен",
        status.HTTP_404_NOT_FOUND: "Отправка не найдена",
        status.HTTP_405_METHOD_NOT_ALLOWED: "Удаление возможно только для отправки в статусе 'Черновик'",
    },
)

# DELETE удаление
@api_view(["DELETE"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def delete_shipment(request, shipment_id):
    try:
        shipment = Shipment.objects.get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return Response({"Ошибка": "Отправка не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if not request.user.is_superuser and shipment.owner != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    if shipment.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    shipment.status = 2
    shipment.save()

    serializer = ShipmentsSerializer(shipment, many=False)

    return Response(serializer.data)

@swagger_auto_schema(
    method="delete",
    responses={
        status.HTTP_200_OK: PartSerializer(many=True),
        status.HTTP_403_FORBIDDEN: "Доступ запрещен",
        status.HTTP_404_NOT_FOUND: "Связь между деталью и отправкой не найдена",
    },
)

# DELETE удаление из заявки (без PK м-м)
@api_view(["DELETE"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def delete_part_from_shipment(request, shipment_id, part_id):
    try:
        part_shipment = PartShipment.objects.get(shipment=shipment_id, part=part_id)
    except PartShipment.DoesNotExist:
        return Response({"Ошибка": "Связь между деталью и отправкой не найдена"}, status=status.HTTP_404_NOT_FOUND)

    shipment = Shipment.objects.get(pk=shipment_id)
    if not request.user.is_superuser and shipment.owner != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    part_shipment.delete()
    parts = Part.objects.filter(id__in=PartShipment.objects.filter(shipment=shipment_id).values_list("part", flat=True))

    serializer = PartSerializer(parts, many=True)

    return Response(serializer.data, status=status.HTTP_200_OK)

@swagger_auto_schema(
    method="put",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "quantity": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="Новое количество деталей"
            ),
        },
        required=["quantity"],
        description="Обновлённые данные отправки детали"
    ),
    responses={
        status.HTTP_200_OK: PartShipmentSerializer(),
        status.HTTP_403_FORBIDDEN: "Доступ запрещен",
        status.HTTP_404_NOT_FOUND: "Отправка детали не найдена",
        status.HTTP_400_BAD_REQUEST: "Количество не предоставлено",
    },
)

#PUT изменение количества/порядка/значения в м-м (без PK м-м)

@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def update_part_shipment(request, shipment_id, part_id):
    try:
        part_shipment = PartShipment.objects.get(shipment=shipment_id, part=part_id)
    except PartShipment.DoesNotExist:
        return Response({"Ошибка": "Отправка детали не найдена"}, status=status.HTTP_404_NOT_FOUND)


    shipment = Shipment.objects.get(pk=shipment_id)
    if not request.user.is_superuser and shipment.owner != request.user:
        return Response(status=status.HTTP_403_FORBIDDEN)
    
    quantity = request.data.get("quantity")

    if quantity is not None:
        part_shipment.quantity = quantity
        part_shipment.save()
        serializer = PartShipmentSerializer(part_shipment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response({"Ошибка": "Количество не предоставлено"}, status=status.HTTP_400_BAD_REQUEST)

@swagger_auto_schema(
    method="post",
    request_body=UserSerializer,
    responses={
        status.HTTP_201_CREATED: "Created",
        status.HTTP_400_BAD_REQUEST: "Bad Request",
    },
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method="post",
    manual_parameters=[
        openapi.Parameter(
            "username",
            type=openapi.TYPE_STRING,
            description="username",
            in_=openapi.IN_FORM,
            required=True,
        ),
        openapi.Parameter(
            "password",
            type=openapi.TYPE_STRING,
            description="password",
            in_=openapi.IN_FORM,
            required=True,
        ),
    ],
    responses={
        status.HTTP_200_OK: openapi.Response(
            description="User successfully logged in",
            schema=UserSerializer()
        ),
        status.HTTP_400_BAD_REQUEST: openapi.Response(
            description="Invalid credentials",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "error": openapi.Schema(type=openapi.TYPE_STRING)
                }
            )
        ),
    },
)
@api_view(["POST"])
@parser_classes((FormParser,))
@permission_classes([AllowAny])
def login(request):
    username = request.POST.get("username")
    password = request.POST.get("password")
    user = authenticate(username=username, password=password)

    if user is not None:
        session_id = str(uuid.uuid4())
        session_storage.set(session_id, str(user.id))

        serializer = UserSerializer(user)

        response = Response(serializer.data, status=status.HTTP_200_OK)
        response.set_cookie("session_id", session_id, samesite="lax")
        return response

    return Response(
        {"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST
    )


@swagger_auto_schema(
    method="post",
    responses={
        status.HTTP_204_NO_CONTENT: "No content",
        status.HTTP_403_FORBIDDEN: "Forbidden",
    },
)
@api_view(["POST"])
@permission_classes([IsAuth])
def logout(request):
    session_id = request.COOKIES["session_id"]
    print(session_id)
    if session_storage.exists(session_id):
        session_storage.delete(session_id)
        response = Response(status=status.HTTP_204_NO_CONTENT) 
        response.delete_cookie("session_id") 
        return response 
    return Response(status=status.HTTP_403_FORBIDDEN)


@swagger_auto_schema(
    method="put",
    request_body=UserSerializer,
    responses={
        status.HTTP_200_OK: UserSerializer(),
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_403_FORBIDDEN: "Forbidden",
    },
)
@api_view(["PUT"])
@permission_classes([IsAuth])
@authentication_classes([AuthBySessionID])
def update_user(request):
    cleaned_data = {key: value for key, value in request.data.items() if value != ""}
    print("Received cleaned request data:", cleaned_data)
    
    serializer = UserSerializer(request.user, data=cleaned_data, partial=True)
    if serializer.is_valid():
        print("Validated successfully")
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)