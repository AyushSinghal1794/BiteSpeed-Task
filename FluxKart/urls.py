from django.urls import path
from .views import identify, HomePage

urlpatterns = [
    path('', HomePage, name='home'),
    path('identify', identify, name='identify'),
]
