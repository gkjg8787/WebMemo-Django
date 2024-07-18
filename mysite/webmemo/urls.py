from django.urls import path
from . import views

app_name = 'webmemo'

urlpatterns = [
    path('', views.index, name='index'),
    path('<int:memo_id>/', views.edit,name="edit"),
]