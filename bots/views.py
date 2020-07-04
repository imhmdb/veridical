from django.http import HttpResponse
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from bots import whatsapp, telegram


class TelegramWebHook(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if request.content_type == 'application/json':
            telegram.process_request_body(request.body.decode('UTF-8'))
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class WhatAppWebHook(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        if request.content_type == 'application/x-www-form-urlencoded':
            return HttpResponse(
                whatsapp.process_request_data(request.data),
                content_type='text/xml',
            )
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)
