from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # Pagamentos
    path('pagamentos/', views.PagamentoListView.as_view(), name='pagamento_list'),
    path('pagamentos/novo/', views.PagamentoCreateView.as_view(), name='pagamento_create'),
    path('pagamentos/<int:pk>/editar/', views.PagamentoUpdateView.as_view(), name='pagamento_update'),
    # Para exclusão, adicione se necessário:
    # path('pagamentos/<int:pk>/excluir/', views.PagamentoDeleteView.as_view(), name='pagamento_delete'),
]