from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from .models import *
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view
from django.utils import timezone
from django.contrib.auth import authenticate
from .minio import *


def get_draft_shipment():
    return Shipment.objects.filter(status=1).first()

def get_user():
    return User.objects.filter(is_superuser=False).first()


def get_moderator():
    return User.objects.filter(is_superuser=True).first()

# GET список. В списке услуг возвращается id заявки-черновика этого пользователя для страницы заявки в статусе черновик

@api_view(["GET"])
def get_parts_list(request):
    part_name = request.GET.get("part_name", "")

    parts = Part.objects.filter(status=True).filter(part_name__icontains=part_name)

    serializer = PartSerializer(parts, many=True)

    draft_shipment = get_draft_shipment()

    response = {
        "parts": serializer.data,
        "draft_shipment": draft_shipment.pk if draft_shipment else None
    }

    return Response(response, status=status.HTTP_200_OK)

# GET одна запись
@api_view(["GET"])
def get_part_by_id(request, part_id):
    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return Response({"Ошибка": "Деталь не найдена"}, status=status.HTTP_404_NOT_FOUND)

    serializer = PartSerializer(part, many=False)

    return Response(serializer.data)

# POST добавление
@api_view(["POST"])
def create_part(request):
    # Извлекаем данные, исключая поле image
    part_data = request.data.copy()
    part_data.pop('image', None)  # Удаляем image из данных, если оно есть
    
    serializer = PartSerializer(data=part_data)
    serializer.is_valid(raise_exception=True)  # Проверка валидности с автоматической обработкой ошибок

    new_part = serializer.save()  # Сохраняем новую деталь

    # Загружаем изображение, если оно есть в запросе
    pic = request.FILES.get("image")
    if pic:
        pic_result = add_pic(new_part, pic)
        if 'error' in pic_result.data:
            return pic_result  # Возвращаем ошибку, если загрузка изображения не удалась

    # Обновляем и возвращаем данные с новой деталью
    return Response(PartSerializer(new_part).data, status=status.HTTP_201_CREATED)

@api_view(["PUT"])
def update_part(request, part_id):
    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return Response({"Ошибка": "Деталь не найдена"}, status=status.HTTP_404_NOT_FOUND)

    # Извлекаем данные, исключая поле image
    part_data = request.data.copy()
    part_data.pop('image', None)  # Удаляем image из данных, если оно есть

    serializer = PartSerializer(part, data=part_data, partial=True)
    serializer.is_valid(raise_exception=True)  # Проверка валидности с автоматической обработкой ошибок
    updated_part = serializer.save()  # Сохраняем обновлённую деталь
    # Обработка изменения изображения, если оно предоставлено
    pic = request.FILES.get("image")
    if pic:
        pic_result = add_pic(updated_part, pic)
        if 'error' in pic_result.data:
            return pic_result  # Возвращаем ошибку, если загрузка изображения не удалась

    # Возвращаем обновлённые данные детали
    return Response(PartSerializer(updated_part).data, status=status.HTTP_200_OK)

# DELETE удаление. Удаление изображения встроено в метод удаления услуги
@api_view(["DELETE"])
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

#POST добавления в заявку-черновик. Заявка создается пустой, указывается автоматически создатель, дата создания и статус, 
# остальные поля указываются через PUT или смену статуса

@api_view(["POST"])
def add_part_to_shipment(request, part_id):
    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return Response({"error": "Деталь не найдена"}, status=status.HTTP_404_NOT_FOUND)

    draft_shipment = get_draft_shipment()

    if draft_shipment is None:
        draft_shipment = Shipment.objects.create(
            owner=get_user(),
            creation_date=timezone.now()
        )
        draft_shipment.save()

    # Проверяем наличие связки детали и черновика, чтобы не дублировать её
    if PartShipment.objects.filter(shipment=draft_shipment, part=part).exists():
        return Response({"error": "Деталь уже добавлена в черновик"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    # Создаем связку между деталью и отправкой
    try:
        part_shipment = PartShipment.objects.create(
            shipment=draft_shipment,
            part=part
        )
    except Exception as e:
        return Response({"error": f"Ошибка при создании связки: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Сериализуем черновик и возвращаем ответ
    serializer = ShipmentSerializer(draft_shipment)
    return Response(serializer.data.get("ships", []), status=status.HTTP_200_OK)

# POST добавление изображения. Добавление изображения по id услуги, старое изображение заменяется/удаляется
@api_view(["POST"])
def update_part_image(request, part_id):
    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return Response({"Ошибка": "Деталь не найдена"}, status=status.HTTP_404_NOT_FOUND)

    image = request.FILES.get("image")
    
    if image is not None:
        # Заменяем старое изображение
        pic_result = add_pic(part, image)  # Используем функцию add_pic для загрузки нового изображения
        if 'error' in pic_result.data:
            return pic_result  # Если произошла ошибка, возвращаем её
        
        serializer = PartSerializer(part)  # Обновляем сериализатор
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response({"Ошибка": "Изображение не предоставлено"}, status=status.HTTP_400_BAD_REQUEST)

# GET список (кроме удаленных и черновика, модератор и создатель через логины)
@api_view(["GET"])
def get_shipments_list(request):
    status = int(request.GET.get("status", 0))
    date_formation_start = request.GET.get("date_formation_start")
    date_formation_end = request.GET.get("date_formation_end")

    shipments = Shipment.objects.exclude(status__in=[1, 2])

    if status > 0:
        shipments = shipments.filter(status=status)

    if date_formation_start and parse_datetime(date_formation_start):
        shipments = shipments.filter(formation_date__gte=parse_datetime(date_formation_start))

    if date_formation_end and parse_datetime(date_formation_end):
        shipments = shipments.filter(formation_date__lt=parse_datetime(date_formation_end))

    serializer = ShipmentSerializer(shipments, many=True)

    return Response(serializer.data)

# GET одна запись (поля заявки + ее услуги). При получении заявки возвращается список ее услуг с картинками
@api_view(["GET"])
def get_shipment_by_id(request, shipment_id):
    try:
        shipment = Shipment.objects.get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return Response({"Ошибка": "Отправка не найдена"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ShipmentSerializer(shipment, many=False)

    return Response(serializer.data)

# PUT изменение доп. полей заявки
@api_view(["PUT"])
def update_shipment(request, shipment_id):
    try:
        shipment = Shipment.objects.get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return Response({"Ошибка": "Отправка не найдена"}, status=status.HTTP_404_NOT_FOUND)

    allowed_fields = ['planned_date', 'storage', 'operation_type']

    data = {key: value for key, value in request.data.items() if key in allowed_fields}

    if not data:
        return Response({"Ошибка": "Нет данных для обновления или поля не разрешены"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ShipmentSerializer(shipment, data=data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# PUT сформировать создателем. Происходит проверка на обязательные поля
@api_view(["PUT"])
def update_status_user(request, shipment_id):
    try:
        shipment = Shipment.objects.get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return Response({"Ошибка": "Отправка не найдена"}, status=status.HTTP_404_NOT_FOUND)

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

    serializer = ShipmentSerializer(shipment, many=False)
    return Response(serializer.data, status=status.HTTP_200_OK)

# PUT завершить/отклонить модератором
@api_view(["PUT"])
def update_status_admin(request, shipment_id):
    try:
        shipment = Shipment.objects.get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return Response({"Ошибка": "Отправка не найдена"}, status=status.HTTP_404_NOT_FOUND)

    request_status = int(request.data["status"])

    if request_status not in [4, 5]:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    if shipment.status != 3:
        return Response({"Ошибка": "Отправка ещё не сформирована"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    shipment.completion_date = timezone.now()
    shipment.status = request_status
    shipment.moderator = get_moderator()
    shipment.save()

    serializer = ShipmentSerializer(shipment, many=False)

    return Response(serializer.data)

# DELETE удаление
@api_view(["DELETE"])
def delete_shipment(request, shipment_id):
    try:
        shipment = Shipment.objects.get(pk=shipment_id)
    except Shipment.DoesNotExist:
        return Response({"Ошибка": "Отправка не найдена"}, status=status.HTTP_404_NOT_FOUND)

    if shipment.status != 1:
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    shipment.status = 2
    shipment.save()

    serializer = ShipmentSerializer(shipment, many=False)

    return Response(serializer.data)

# DELETE удаление из заявки (без PK м-м)
@api_view(["DELETE"])
def delete_part_from_shipment(request, part_shipment_id, shipment_id):
    if not PartShipment.objects.filter(pk=part_shipment_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    part_shipment = PartShipment.objects.get(pk=part_shipment_id)
    part_shipment.delete()

    shipment = Shipment.objects.get(pk=shipment_id)

    serializer = ShipmentSerializer(shipment, many=False)
    parts_serializer = PartShipmentSerializer(shipment.parts.all(), many=True)

    return Response(
        {"shipment": serializer.data, "parts": parts_serializer.data},
        status=status.HTTP_200_OK
    )

#PUT изменение количества/порядка/значения в м-м (без PK м-м)

@api_view(["PUT"])
def update_part_shipment(request, part_shipment_id):
    try:
        part_shipment = PartShipment.objects.get(pk=part_shipment_id)
    except PartShipment.DoesNotExist:
        return Response({"Ошибка": "Отгрузка детали не найдена"}, status=status.HTTP_404_NOT_FOUND)

    quantity = request.data.get("quantity")

    if quantity is not None:
        part_shipment.quantity = quantity
        part_shipment.save()
        serializer = PartShipmentSerializer(part_shipment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response({"Ошибка": "Количество не предоставлено"}, status=status.HTTP_400_BAD_REQUEST)


#POST регистрация

@api_view(["POST"])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    user = serializer.save()

    serializer = UserSerializer(user)

    return Response(serializer.data, status=status.HTTP_201_CREATED)

#PUT пользователя (личный кабинет)

@api_view(["PUT"])
def update_user(request, user_id):
    if not User.objects.filter(pk=user_id).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    user = User.objects.get(pk=user_id)
    serializer = UserSerializer(user, data=request.data, many=False, partial=True)

    if not serializer.is_valid():
        return Response(status=status.HTTP_409_CONFLICT)

    serializer.save()

    return Response(serializer.data)

#POST аутентификация

@api_view(["POST"])
def login(request):
    serializer = UserLoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(**serializer.data)
    if user is None:
        return Response(status=status.HTTP_401_UNAUTHORIZED)

    return Response(status=status.HTTP_200_OK)


@api_view(["POST"])
def logout(request):
    return Response(status=status.HTTP_200_OK)