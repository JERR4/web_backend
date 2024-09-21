from django.contrib.auth.models import User
from django.db import connection
from app.models import Part, Order, PartOrder
from django.shortcuts import render, redirect
from django.utils import timezone

def index(request):
    part_name = request.GET.get("part_name", "")
    
    # Поиск деталей по названию
    if part_name:
        parts = Part.objects.filter(part_name__icontains=part_name)
    else:
        parts = Part.objects.all()
    
    draft_order = get_draft_order()
    context = {
        'parts': parts,
        'part_name': part_name,
    }

    if draft_order:
        context["parts_in_processing"] = len(draft_order.get_parts())
        context["draft_order"] = draft_order
        context["parts_in_draft_order"] = PartOrder.objects.filter(order=draft_order).values_list('part_id', flat=True)
    
    return render(request, 'index.html', context)

def add_part_to_draft_order(request, part_id):
    part = Part.objects.get(pk=part_id)

    draft_order = get_draft_order()

    if draft_order is None:
        draft_order = Order.objects.create(
            creation_date=timezone.now(),
            owner=get_current_user()
        )
        draft_order.save()

    if PartOrder.objects.filter(order=draft_order, part=part).exists():
        return redirect(f"/?part_name={request.POST.get('part_name', '')}")

    p_o = PartOrder(
        order=draft_order,
        part=part
    )
    p_o.save()

    return redirect(f"/?part_name={request.POST.get('part_name', '')}")

def part(request, part_id):
    # Получение детали по id
    return render(request, "part.html", {'part':  Part.objects.get(id=part_id)})

def orders(request, order_id):
    return render(request, "orders.html", {"order": Order.objects.get(id=order_id)})

def get_draft_order():
    return Order.objects.filter(status=1).first()

def get_current_user():
    return User.objects.filter(is_superuser=False).first()

def delete(request, order_id):
    with connection.cursor() as cursor:
        cursor.execute("UPDATE orders SET status = 2 WHERE id = %s", [order_id])
    return redirect("/")
