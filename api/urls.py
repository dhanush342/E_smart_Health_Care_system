from django.contrib import admin
from django.urls import path ,include
from django.conf.urls import url
from django.views.generic.base import RedirectView
from rest_framework import routers
from api import views

router = routers.DefaultRouter()
router.register(r'disease', views.DiseaseViewSet, basename='disease')
router.register(r'api', views.DiseaseViewSet, basename='api-disease')

urlpatterns = [
    path('', include(router.urls)),
]
