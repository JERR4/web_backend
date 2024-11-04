from django.db import models
from django.contrib.auth.models import User

class Part(models.Model):
    STATUS_CHOICES = [
        (True, 'Действует'),
        (False, 'Удален'),
    ]
    
    part_name = models.CharField(max_length=100, verbose_name="Название детали")
    specification = models.CharField(max_length=50, verbose_name="Спецификация")
    oem_number = models.CharField(max_length=50, unique=True, verbose_name="OEM номер")
    status = models.BooleanField(choices=STATUS_CHOICES, default=True, verbose_name="Статус")
    image = models.URLField(verbose_name="Изображение", blank=True, null=True)
    short_description = models.TextField(max_length=800, verbose_name="Краткое описание",  blank=True)
    set_composition = models.TextField(max_length=1200, verbose_name="Состав набора",  blank=True)
    dimensions = models.CharField(max_length=50, verbose_name="Размеры")
    weight = models.FloatField(verbose_name="Вес")
    
    class Meta:
        db_table = "parts"
        verbose_name = "Деталь"
        verbose_name_plural = "Детали"

# Модель для таблицы 'shipments'
class Shipment(models.Model):
    STATUS_CHOICES = [
        (1, 'Черновик'),
        (2, 'Удален'),
        (3, 'Сформирован'),
        (4, 'Завершён'),
        (5, 'Отклонён'),
    ]
    OPERATION_TYPE_CHOICES = [
        (True, 'Доставка'),
        (False, 'Отгрузка'),
    ]
    
    status = models.IntegerField(choices=STATUS_CHOICES, default=1,verbose_name="Статус")
    creation_date = models.DateTimeField(verbose_name="Дата создания")
    formation_date = models.DateTimeField(verbose_name="Дата формирования", blank=True, null=True)
    planned_date = models.DateField(verbose_name="Дата запланированного завершения", blank=True, null=True)
    completion_date = models.DateTimeField(verbose_name="Дата завершения", blank=True, null=True)
    storage = models.CharField(max_length=50, verbose_name="Название склада", blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", null=True, related_name='owner')
    moderator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Модератор", null=True, related_name='moderator')
    operation_type = models.BooleanField(choices=OPERATION_TYPE_CHOICES, null=True, blank=True, verbose_name="Тип операции")
    license_plate_number =  models.CharField(max_length=10, verbose_name="Номер автомобиля", blank=True, null=True)

    def __str__(self):
        if self.owner:
            return f"Shipment {self.id} by {self.owner.username}"
        else:
            return f"Dispatc{self.id} (No owner)"
    
    def get_status(self):
        return self.STATUS_CHOICES.get(self.status)

    def get_parts(self):
            res = []

            for part_shipment in PartShipment.objects.filter(shipment=self):
                tmp = part_shipment.part
                tmp.quantity = part_shipment.quantity
                res.append(tmp)

            return res
    
    class Meta:
        verbose_name = "Отправка"
        verbose_name_plural = "Отправка"
        db_table = "shipments"

# Модель для таблицы 'part-shipment'
class PartShipment(models.Model):
    shipment = models.ForeignKey(Shipment, on_delete=models.CASCADE, verbose_name="Отправка")
    part = models.ForeignKey(Part, on_delete=models.CASCADE, verbose_name="Деталь")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Поле М-М")

    def __str__(self):
        return f"Shipment {self.shipment.id} - Part {self.part.part_name} (Qty: {self.quantity})"

    class Meta:
        db_table = "part_shipment"
        verbose_name = "М-М"
        verbose_name_plural = "М-М"
        unique_together = ('shipment', 'part')