from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.models import User

from .models import (
    Image,
    Text,
    TRUTHFULNESS_POINTS_TRUTH_IS_GREATER_THAN_VALUE,
    TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE,
)
from .utils import get_image_hash

admin.site.site_header = 'Veridical'


class ImageForm(forms.ModelForm):
    image = forms.ImageField()
    is_rumor = forms.BooleanField(initial=False, required=False)


class ImageAdmin(admin.ModelAdmin):
    form = ImageForm
    list_display = (
        "original_hash",
        "is_rumor",
        'reviews',
    )
    fieldsets = (
        (None, {
            'fields': ('image', 'is_rumor'),
        }),
    )

    def has_change_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        is_rumor = form.cleaned_data['is_rumor']
        img_hash = get_image_hash(form.cleaned_data['image'])
        obj, _ = Image.objects.first_or_create(original_hash=img_hash)
        obj.truthfulness_points = (
            TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE - 1
            if
            is_rumor
            else
            TRUTHFULNESS_POINTS_TRUTH_IS_GREATER_THAN_VALUE + 1
        )
        return obj.save()

    def reviews(self, obj):
        return ", ".join([p.chat_id for p in obj.reviews.all()])

    def is_rumor(self, obj):
        return obj.truthfulness_points < TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE


class TextForm(forms.ModelForm):
    is_rumor = forms.BooleanField(initial=False, required=False)


class TextAdmin(admin.ModelAdmin):
    form = TextForm
    list_display = (
        "content",
        "is_rumor",
        'reviews',
    )
    fieldsets = (
        (None, {
            'fields': ('content', 'is_rumor'),
        }),
    )

    def has_change_permission(self, request, obj=None):
        return False

    def reviews(self, obj):
        return ", ".join([p.chat_id for p in obj.reviews.all()])

    def is_rumor(self, obj):
        return obj.truthfulness_points < TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE

    def save_model(self, request, obj, form, change):
        obj.truthfulness_points = (
            TRUTHFULNESS_POINTS_LIE_IS_LESS_THAN_VALUE - 1
            if
            form.cleaned_data['is_rumor']
            else
            TRUTHFULNESS_POINTS_TRUTH_IS_GREATER_THAN_VALUE + 1
        )
        return super().save_model(request, obj, form, change)


admin.site.register(Image, ImageAdmin)
admin.site.register(Text, TextAdmin)
admin.site.unregister(User)
admin.site.unregister(Group)
