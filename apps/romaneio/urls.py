from django.urls import path
from . import views

app_name = 'romaneio'

urlpatterns = [
    path('', views.RomaneioListView.as_view(), name='romaneio_list'),
    path('novo/', views.RomaneioCreateView.as_view(), name='romaneio_create'),
    path('<int:pk>/', views.RomaneioDetailView.as_view(), name='romaneio_detail'),
    path('<int:pk>/editar/', views.RomaneioUpdateView.as_view(), name='romaneio_update'),

    # API utilitária
    path('api/preco-madeira/', views.get_preco_madeira, name='get_preco_madeira'),
]