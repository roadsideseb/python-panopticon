from django.conf.urls import url

from .views import HealthCheckView


urlpatterns = [
    url(r'^healthcheck/$', HealthCheckView.as_view(), name='healthcheck'),
]
