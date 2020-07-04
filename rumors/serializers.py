import hashlib

from rest_framework import serializers

from rumors.models import Image, Text
from rumors.utils import get_image_hash


class ImageSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)

    def create(self, validated_data):
        file = validated_data['file']
        img_hash = get_image_hash(file)
        obj, _ = Image.objects.first_or_create(original_hash=img_hash)
        return obj


class ImageValiditySerializer(serializers.Serializer):
    file = serializers.FileField(required=True)


class TextSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        obj, _ = Text.objects.get_or_create(
            content=validated_data['content'],
            content_md5=hashlib.md5(validated_data['content'].encode('utf-8')).hexdigest()
        )
        return obj

    class Meta:
        model = Text
        fields = (
            "content",
        )
