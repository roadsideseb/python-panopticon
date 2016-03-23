# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from ..health import HealthCheck


class HealthCheckView(APIView):
    permission_classes = []

    def get(self, request, *args, **kwargs):
        health_check = HealthCheck()
        result = health_check.run()

        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        if result.is_healthy:
            status_code = status.HTTP_200_OK

        return Response(result.data, status=status_code)
