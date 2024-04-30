from django.urls import path
from django.views.generic import TemplateView
from . import views
from .views import Index  # Ensure you're importing the Index view

app_name = 'items'
urlpatterns = [
    path('report/lost/', views.ReportItemView.as_view(is_found=False), name='report_lost'),
    path('report/found/', views.ReportItemView.as_view(is_found=True), name='report_found'),
    path('report/success/', TemplateView.as_view(template_name='items/report_success.html'), name='report_success'),
    path("<int:id>/", views.Detail.as_view(), name='details'),
    path('<int:id>/delete', views.delete, name='delete'),
    path('<int:id>/flag', views.flag, name='flag'),
    path('lost/', views.Index.as_view(is_found=False), name='index_lost'),
    path('found/', views.Index.as_view(is_found=True), name='index_found'),
    path('locations', views.getLocations, name='locations'),
]
