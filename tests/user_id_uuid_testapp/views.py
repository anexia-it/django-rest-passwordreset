from rest_framework import viewsets

from drf_anonymous_login.views import AnonymousLoginAuthenticationModelViewSet

from .models import PrivateModel, PublicModel
from .serializers import PrivateModelSerializer, PublicModelSerializer


class PublicModelViewSet(viewsets.ModelViewSet):
    queryset = PublicModel.objects.all()
    serializer_class = PublicModelSerializer


class PrivateModelViewSet(AnonymousLoginAuthenticationModelViewSet):
    queryset = PrivateModel.objects.all()
    serializer_class = PrivateModelSerializer
