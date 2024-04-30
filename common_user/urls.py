from django.urls import path

from . import views

app_name = 'common_user'
urlpatterns = [
    path("history/", views.History.as_view(), name="history"),
]
