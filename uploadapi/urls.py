from django.urls import path
from .views import UploadZipView, DashboardStatsView, DashboardPecasView, DashboardDetalhesPecaView

urlpatterns = [
    path('upload/', UploadZipView.as_view(), name='upload-archive'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/pecas/', DashboardPecasView.as_view(), name='dashboard-pecas'),
    path('dashboard/pecas/<str:codigo_peca>/', DashboardDetalhesPecaView.as_view(), name='dashboard-detalhes-peca'),
] 