from django.urls import path
from .views import UploadZipView

urlpatterns = [
    path('upload/', UploadZipView.as_view(), name='upload-archive'),
] 