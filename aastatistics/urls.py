from django.conf.urls import url

from . import views

app_name = 'aastatistics'

urlpatterns = [
    url(r'^$', views.outputcsv, name='outputcsv'),
]
