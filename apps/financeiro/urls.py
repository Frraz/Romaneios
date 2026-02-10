from django.urls import path

from .views import (
    PagamentoCreateView,
    PagamentoDeleteView,
    PagamentoListView,
    PagamentoUpdateView,
)

app_name = "financeiro"

urlpatterns = [
    path("pagamentos/", PagamentoListView.as_view(), name="pagamento_list"),
    path("pagamentos/novo/", PagamentoCreateView.as_view(), name="pagamento_create"),
    path("pagamentos/<int:pk>/editar/", PagamentoUpdateView.as_view(), name="pagamento_update"),
    path("pagamentos/<int:pk>/excluir/", PagamentoDeleteView.as_view(), name="pagamento_delete"),
]