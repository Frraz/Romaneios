from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    path('pagamentos/', views.PagamentoListView.as_view(), name='pagamento_list'),
    path('pagamentos/novo/', views.PagamentoCreateView.as_view(), name='pagamento_create'),
    path('pagamentos/<int:pk>/editar/', views.PagamentoUpdateView.as_view(), name='pagamento_update'),
]