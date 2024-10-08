"""
URL configuration for lab3 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from app.views import *
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('app/', include(router.urls)),
    path('admin/', admin.site.urls),

    path('api/parts/search/', get_parts_list, name='get_parts_list'),  # GET
    path('api/parts/<int:part_id>/',get_part_by_id, name='get_part_by_id'),  # GET
    path('api/parts/create/', create_part, name='create_part'),  # POST
    path('api/parts/<int:part_id>/update/', update_part, name='update_part'),  # PUT
    path('api/parts/<int:part_id>/delete/', delete_part, name='delete_part'),  # DELETE
    path('api/parts/<int:part_id>/add_to_shipment/',add_part_to_shipment, name='add_part_to_shipment'),  # POST
    path('api/parts/<int:part_id>/update_image/', update_part_image, name='update_part_image'),  # PUT

    # Набор методов для заявок
    path('api/shipments/search/',  get_shipments_list, name=' get_shipments_list'),  # GET
    path('api/shipments/<int:shipment_id>/', get_shipment_by_id, name='get_shipment_by_id'),  # GET
    path('api/shipments/<int:shipment_id>/update/', update_shipment, name='update_shipment'),  # PUT
    path('api/shipments/<int:shipment_id>/update_status_user/', update_status_user, name='update_status_user'),  # PUT
    path('api/shipments/<int:shipment_id>/update_status_admin/', update_status_admin, name='update_status_admin'),  # PUT
    path('api/shipments/<int:shipment_id>/delete/', delete_shipment, name='delete_shipment'),  # DELETE

    # Набор методов для м-м
    path('api/part_shipments/<int:part_shipment_id>/', update_part_shipment, name='update_part_shipment'),  # PUT
    path('api/part_shipments/<int:part_shipment_id>/', delete_part_from_shipment, name='update_part_shipment'),  # DELETE

    # Набор методов пользователей
    path('api/users/register/', register, name='register'),  # POST
    path('api/users/login/', login, name='login'),  # POST
    path('api/users/logout/', logout, name='logout'),  # POST
    path('api/users/<int:user_id>/update/', update_user, name='update_user'),  # PUT
]