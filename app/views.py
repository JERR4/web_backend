from django.shortcuts import render, get_object_or_404
from data import PARTS_DATA
from draft_shipment import DRAFT_SHIPMENT

def index(request):
    part_name = request.GET.get("part_name", "") 
    parts = search_part(part_name) 
    parts_in_processing = sum(1 for part in DRAFT_SHIPMENT['parts'])
    return render(request, 'index.html', {
        'parts': parts, 
        'part_name': part_name,  
        "draft_shipment_id": DRAFT_SHIPMENT["id"],
        'parts_in_processing': parts_in_processing
    })

def part(request, part_id):
    part = get_part_by_id(part_id)
    if not part:
        return render(request, '404.html', status=404)
    return render(request, "part.html", {'part': part})

def shipments(request, shipment_id):
    shipment = getShipmentById(shipment_id)  # Получаем заказ
    return render(request, "shipments.html", {"shipment": shipment})
    

def get_part_by_id(part_id):
    for part in PARTS_DATA:
        if part['id'] == part_id:
            return part
    return None

def search_part(part_name):
    res = []
    for part in PARTS_DATA:
        if part_name.lower() in part["name"].lower():
            res.append(part)
    return res

def getShipmentById(shipment_id):
    return DRAFT_SHIPMENT