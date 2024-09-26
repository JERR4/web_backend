from django.contrib.auth.models import User
from django.db import connection
from app.models import Part, Shipment, PartShipment
from django.shortcuts import render, redirect
from django.utils import timezone

def index(request):
    part_name = request.GET.get("part_name", "")
    
    # Поиск деталей по названию
    if part_name:
        parts = Part.objects.filter(part_name__icontains=part_name)
    else:
        parts = Part.objects.all()
    
    draft_shipment = get_draft_shipment()
    context = {
        'parts': parts,
        'part_name': part_name,
    }

    if draft_shipment:
        context["parts_in_processing"] = len(draft_shipment.get_parts())
        context["draft_shipment"] = draft_shipment
        parts_in_draft_shipment = PartShipment.objects.filter(shipment=draft_shipment).values_list('part_id', flat=True)
        
        for part in parts:
            part.added = part.id in parts_in_draft_shipment
    
    return render(request, 'index.html', context)

def add_part_to_draft_shipment(request, part_id):
    part = Part.objects.get(pk=part_id)

    draft_shipment = get_draft_shipment()

    if draft_shipment is None:
        draft_shipment = Shipment.objects.create(
            creation_date=timezone.now(),
            owner=get_current_user()
        )
        draft_shipment.save()

    if PartShipment.objects.filter(shipment=draft_shipment, part=part).exists():
        part_name = request.POST.get('part_name', '')
        if part_name:
            return redirect(f"/?part_name={part_name}")
        else:
            return redirect("/")

    part_shipment = PartShipment(
        shipment=draft_shipment,
        part=part
    )
    part_shipment.save()

    part_name = request.POST.get('part_name', '')
    if part_name:
        return redirect(f"/?part_name={part_name}")
    else:
        return redirect("/")


def part(request, part_id):
    # Получение детали по id
    return render(request, "part.html", {'part':  Part.objects.get(id=part_id)})

def shipments(request, shipment_id):
    if Shipment.objects.get(id=shipment_id).status == 2:
        return redirect("/")
    return render(request, "shipments.html", {"shipment": Shipment.objects.get(id=shipment_id)})

def get_draft_shipment():
    return Shipment.objects.filter(status=1).first()

def get_current_user():
    return User.objects.filter(is_superuser=False).first()

def delete(request, shipment_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE shipments SET status = 2 WHERE id = %s", [shipment_id])
    return redirect("/")
