from django.conf.urls import url, include


urlpatterns = [
    url(r'', include('panopticon.django.urls', namespace='panopticon')),
]
