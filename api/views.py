from django.shortcuts import render
from rest_framework import viewsets
from . models import Disease
from api.serializers import DiseaseSerializer
from . import diseaseml
from rest_framework.response import Response
from django.contrib.auth.models import User


# Create your views here.
class DiseaseViewSet(viewsets.ModelViewSet):
    queryset=Disease.objects.all().order_by('-id')
    serializer_class=DiseaseSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        ob = serializer.instance
        pred_res, symptoms = diseaseml.pred(ob)
        disease_name = pred_res[0] if (hasattr(pred_res, '__len__') and len(pred_res) > 0) else str(pred_res)
        return Response({
            "status": "Success",
            "Disease": disease_name,
            "prediction": disease_name,
            "symptoms": list(symptoms),
            "data": serializer.data
        })
