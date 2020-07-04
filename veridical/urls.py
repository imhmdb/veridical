from django.conf.urls import url, include
from django.http import HttpResponse
from django.urls import path
from rest_framework import routers
from django.contrib import admin

from bots.views import TelegramWebHook, WhatAppWebHook
from rumors.views import ImageViewSet, TextViewSet
from django.conf import settings


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'images', ImageViewSet)
router.register(r'texts', TextViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    url(r'^v1/', include(router.urls)),
    path('backoffice/', admin.site.urls),
    path('v1/bots/telegram/'+settings.TELEGRAM_BOT_TOKEN, TelegramWebHook.as_view(), name='index'),
    path('v1/bots/whatsapp', WhatAppWebHook.as_view(), name='index'),
    path('healthz/', lambda request: HttpResponse("ok")),
]
