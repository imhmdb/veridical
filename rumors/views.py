from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from rumors.models import Image, Text
from rumors.serializers import ImageSerializer, ImageValiditySerializer, TextSerializer
from rumors.utils import check_if_image_exists_and_is_rumor


class ImageViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Image.objects.all()
    http_method_names = ['post', 'head']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    @action(
        ["POST"],
        detail=False,
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
        url_path="validate-image"
    )
    def validate_image(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        return Response(status=status.HTTP_200_OK, data={
            'is_rumor': check_if_image_exists_and_is_rumor(file)
        })

    def get_serializer_class(self):
        if self.action == "create":
            return ImageSerializer
        elif self.action == "validate_image":
            return ImageValiditySerializer


class TextViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Text.objects
    http_method_names = ['post', 'head']

    @action(
        ["POST"],
        detail=False,
        permission_classes=[permissions.IsAuthenticatedOrReadOnly],
        url_path="validate-text"
    )
    def validate_text(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exists = self.get_queryset().similar(serializer.validated_data['content']).exists()
        return Response(status=status.HTTP_200_OK, data={
            'is_rumor': exists
        })

    def get_serializer_class(self):
        return TextSerializer
