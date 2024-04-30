from django.urls import path

from items.models import Status
from . import views

app_name = 'site_admin'
urlpatterns = [
    path("", views.review_redirect),
    path("review/", views.ReviewItems.as_view(), name="review"),
    path("review/<int:id>/", views.Detail.as_view(), name="detail"),
    path("review/<int:id>/reject/", views.Resolve.as_view(status=Status.REJECTED), name="remove"),
    path("review/<int:id>/resolve/", views.Resolve.as_view(status=Status.RESOLVED), name="resolve"),
    path("review/<int:id>/update/", views.update, name="update"),
]
