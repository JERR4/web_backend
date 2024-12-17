"""
URL configuration for book_office_project project.

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
from django.urls import path

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from app.views import *

schema_view = get_schema_view(
    openapi.Info(
        title="Parts storage API",
        default_version="v1",
        description="API for parts storage",
        contact=openapi.Contact(email="yaroslav.auto@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path('parts/search/', get_parts_list, name='get_parts_list'),  # GET
    path('parts/<int:part_id>/',get_part_by_id, name='get_part_by_id'),  # GET
    path('parts/create/', create_part, name='create_part'),  # POST
    path('parts/<int:part_id>/update/', update_part, name='update_part'),  # PUT
    path('parts/<int:part_id>/delete/', delete_part, name='delete_part'),  # DELETE
    path('parts/<int:part_id>/add_to_shipment/',add_part_to_shipment, name='add_part_to_shipment'),  # POST
    path('parts/<int:part_id>/update_image/', update_part_image, name='update_image'),  # POST

    # Набор методов для заявок
    path('shipments/search/',  get_shipments_list, name=' get_shipments_list'),  # GET
    path('shipments/<int:shipment_id>/', get_shipment_by_id, name='get_shipment_by_id'),  # GET
    path('shipments/<int:shipment_id>/update/', update_shipment, name='update_shipment'),  # PUT
    path('shipments/<int:shipment_id>/update_status_user/', update_status_user, name='update_status_user'),  # PUT
    path('shipments/<int:shipment_id>/update_status_admin/', update_status_admin, name='update_status_admin'),  # PUT
    path('shipments/<int:shipment_id>/delete/', delete_shipment, name='delete_shipment'),  # DELETE

    # Набор методов для м-м
    path('shipments/<int:shipment_id>/update_part_shipment/<int:part_id>', update_part_shipment, name='update_part_shipment'),  # PUT
    path('shipments/<int:shipment_id>/delete_part_from_shipment/<int:part_id>', delete_part_from_shipment, name='delete_part_from_shipment'),  # DELETE

    # Набор методов пользователей
    path('users/register/', register, name='register'),  # POST
    path('users/login/', login, name='login'),  # POST
    path('users/logout/', logout, name='logout'),  # POST
    path('users/update/', update_user, name='update_user'),  # PUT
]