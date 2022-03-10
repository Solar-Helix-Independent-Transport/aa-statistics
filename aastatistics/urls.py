from django.urls import re_path
from . import views

app_name = 'aastatistics'

urlpatterns = [
    re_path(r'^$', views.outputcsv, name='outputcsv'),
]
