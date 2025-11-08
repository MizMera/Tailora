from django.urls import path
from .views import EventListView, EventCreateView, EventUpdateView, EventDeleteView

app_name = 'events'

urlpatterns = [
    path('', EventListView.as_view(), name='list'),
    path('create/', EventCreateView.as_view(), name='create'),
    path('<int:pk>/update/', EventUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', EventDeleteView.as_view(), name='delete'),
]
