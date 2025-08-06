from django.urls import path, include
from .views import *


urlpatterns = [
    path('reports/reply/', ReplyToReportAPIView.as_view(), name='reply-to-report'),
]
