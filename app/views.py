from django.shortcuts import render, get_object_or_404
from data import PARTS_DATA
from draft_order import DRAFT_ORDER

def index(request):
    part_name = request.GET.get("part_name", "")  # Use a more descriptive name for the query parameter
    parts = search_part(part_name)  # Search for parts matching the part name
    parts_in_processing = sum(1 for part in DRAFT_ORDER['parts'])
    return render(request, 'index.html', {
        'parts': parts, 
        'part_name': part_name,  # Pass the part name to the template
        'DRAFT_ORDER': DRAFT_ORDER,
        'parts_in_processing': parts_in_processing  # Number of parts in processing
    })

def part(request, part_id):
    part = get_part_by_id(part_id)
    if not part:
        return render(request, '404.html', status=404)
    return render(request, "part.html", {'part': part})

def orders(request, order_id):
    order = getOrderById(order_id)  # Получаем заказ
    return render(request, "orders.html", {"DRAFT_ORDER": order})
    

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

def getOrderById(order_id):
    return DRAFT_ORDER