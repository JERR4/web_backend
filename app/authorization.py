from rest_framework import permissions
from django.contrib.auth.models import User
from .redis import session_storage
from rest_framework import authentication
from rest_framework import exceptions


class AuthBySessionID(authentication.BaseAuthentication):
    def authenticate(self, request):
        session_id = request.COOKIES.get("session_id")
        if session_id is None:
            raise exceptions.AuthenticationFailed("Нет сессии")
        try:
            user_id = session_storage.get(session_id).decode("utf-8")
        except Exception as e:
            raise exceptions.AuthenticationFailed("Сессия с таким ID не найдена в хранилище сессий")
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("Пользователь с таким ID не найден в БД")
        
        return user, None



class AuthBySessionIDIfExists(authentication.BaseAuthentication):
    def authenticate(self, request):
        session_id = request.COOKIES.get("session_id")
        if session_id is None:
            return None, None
        try:
            user_id = session_storage.get(session_id).decode("utf-8")
        except Exception as e:
            return None, None
        user = User.objects.get(id=user_id)
        return user, None


class IsAuth(permissions.BasePermission):
    def has_permission(self, request, view):
        session_id = request.COOKIES.get("session_id")
        if session_id is None:
            return False
        try:
            user_id = session_storage.get(session_id).decode("utf-8")
            user = User.objects.get(id=user_id)
        except Exception as e:
            return False
        return True



class IsManagerAuth(permissions.BasePermission):
    def has_permission(self, request, view):
        session_id = request.COOKIES.get("session_id")
        if session_id is None:
            return False
        try:
            user_id = session_storage.get(session_id).decode("utf-8")
        except Exception as e:
            return False
        user = User.objects.filter(id=user_id).first()
        if user is None:
            return False
        return user.is_superuser