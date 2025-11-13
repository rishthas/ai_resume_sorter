from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('results/<int:session_id>/', views.results, name='results'),
    path('sessions/', views.session_list, name='session_list'),
]
