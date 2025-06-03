from django.urls import path
from .views import LogEntryListCreate, LogEntryDetail, index_view

urlpatterns = [
    path('logs/', LogEntryListCreate.as_view(), name='logentry-list-create'),
    path('logs/<int:pk>/', LogEntryDetail.as_view(), name='logentry-detail'),
    path('', index_view, name='index'),
]