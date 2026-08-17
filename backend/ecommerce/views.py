"""API REST — e-commerce Gesttora."""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from django_tenants.utils import schema_context
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from mandatos.permissions import IsBoardOrAdmin

from .models import Cart, CartItem, CatalogItem, Order, OrderStatus, PaymentMethod
from .permissions import IsMember
from .serializers import (
    CartSerializer,
    CatalogItemSerializer,
    CheckoutSerializer,
    OrderSerializer,
    PublicCatalogItemSerializer,
)
from .services import (
    create_order_from_cart,
    get_or_create_cart,
    process_order_payment,
    resolve_membro_for_ecommerce,
    validate_cart_item_for_membro,
)
from tenants.resolvers import resolve_tenant_from_request


class CatalogItemViewSet(viewsets.ModelViewSet):
    """CRUD catálogo (diretoria) + vitrine ativa (associado)."""

    serializer_class = CatalogItemSerializer
    lookup_field = "slug"

    def get_permissions(self):
        if self.action in ("list", "retrieve", "loja"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsBoardOrAdmin()]

    def get_queryset(self):
        qs = CatalogItem.objects.select_related("evento").all()
        if self.action in ("list", "retrieve") and not IsBoardOrAdmin().has_permission(
            self.request, self
        ):
            qs = qs.filter(is_active=True)
        else:
            active = self.request.query_params.get("is_active")
            if active is not None:
                qs = qs.filter(is_active=active.lower() == "true")
            item_type = self.request.query_params.get("item_type")
            if item_type:
                qs = qs.filter(item_type=item_type)
            search = self.request.query_params.get("search")
            if search:
                qs = qs.filter(
                    Q(name__icontains=search) | Q(description__icontains=search)
                )
        return qs.order_by("name")

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"], url_path="loja")
    def loja(self, request):
        """Vitrine pública autenticada para associados."""
        qs = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Pedidos — diretoria vê todos; associado vê os próprios."""

    serializer_class = OrderSerializer

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Order.objects.prefetch_related(
            "items", "items__catalog_item"
        ).select_related("membro")

        if self.request.user.role == User.MEMBER:
            membro = resolve_membro_for_ecommerce(self.request.user)
            if not membro:
                return Order.objects.none()
            qs = qs.filter(membro=membro)
        elif not IsBoardOrAdmin().has_permission(self.request, self):
            return Order.objects.none()

        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        return qs.order_by("-created_at")

    @action(detail=True, methods=["post"], url_path="confirmar-pagamento")
    def confirmar_pagamento(self, request, pk=None):
        """Diretoria confirma pagamento manual (transferência, boleto)."""
        if not IsBoardOrAdmin().has_permission(request, self):
            raise PermissionDenied("Acesso restrito à diretoria.")
        order = self.get_object()
        if order.status not in (OrderStatus.PENDING,):
            return Response(
                {"detail": "Pedido não está pendente."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            process_order_payment(
                order,
                payment_method=PaymentMethod.MANUAL,
                user=request.user,
            )
        except DjangoValidationError as exc:
            raise ValidationError(exc.message_dict if hasattr(exc, "message_dict") else str(exc))
        return Response(OrderSerializer(order).data)


class CartViewSet(viewsets.ViewSet):
    """Carrinho do associado logado."""

    permission_classes = [IsAuthenticated, IsMember]

    def _membro(self, request):
        membro = resolve_membro_for_ecommerce(request.user)
        if not membro:
            raise PermissionDenied(
                "Perfil de associado não encontrado. Peça à diretoria para vincular seu usuário."
            )
        return membro

    def list(self, request):
        cart = get_or_create_cart(self._membro(request))
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"], url_path="add")
    def add_item(self, request):
        membro = self._membro(request)
        catalog_item_id = request.data.get("catalog_item")
        quantity = int(request.data.get("quantity", 1))
        if not catalog_item_id:
            raise ValidationError({"catalog_item": "Obrigatório."})
        if quantity <= 0:
            raise ValidationError({"quantity": "Deve ser maior que zero."})

        try:
            catalog_item = CatalogItem.objects.get(id=catalog_item_id, is_active=True)
        except CatalogItem.DoesNotExist:
            raise ValidationError({"catalog_item": "Item não encontrado."})

        try:
            validate_cart_item_for_membro(catalog_item, membro, quantity)
        except DjangoValidationError as exc:
            msg = exc.messages[0] if hasattr(exc, "messages") else str(exc)
            raise ValidationError({"detail": msg})

        cart = get_or_create_cart(membro)
        existing = CartItem.objects.filter(cart=cart, catalog_item=catalog_item).first()
        new_qty = (existing.quantity if existing else 0) + quantity
        try:
            validate_cart_item_for_membro(catalog_item, membro, new_qty)
        except DjangoValidationError as exc:
            msg = exc.messages[0] if hasattr(exc, "messages") else str(exc)
            raise ValidationError({"detail": msg})

        if existing:
            existing.quantity = new_qty
            existing.save(update_fields=["quantity", "updated_at"])
        else:
            CartItem.objects.create(cart=cart, catalog_item=catalog_item, quantity=quantity)

        cart.refresh_from_db()
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["patch"], url_path=r"update/(?P<item_id>[^/.]+)")
    def update_item(self, request, item_id=None):
        membro = self._membro(request)
        cart = get_or_create_cart(membro)
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response({"detail": "Item não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        quantity = int(request.data.get("quantity", cart_item.quantity))
        if quantity <= 0:
            cart_item.delete()
        else:
            try:
                validate_cart_item_for_membro(cart_item.catalog_item, membro, quantity)
            except DjangoValidationError as exc:
                msg = exc.messages[0] if hasattr(exc, "messages") else str(exc)
                raise ValidationError({"detail": msg})
            cart_item.quantity = quantity
            cart_item.save(update_fields=["quantity", "updated_at"])

        cart.refresh_from_db()
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["delete"], url_path=r"remove/(?P<item_id>[^/.]+)")
    def remove_item(self, request, item_id=None):
        membro = self._membro(request)
        cart = get_or_create_cart(membro)
        CartItem.objects.filter(id=item_id, cart=cart).delete()
        cart.refresh_from_db()
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"], url_path="clear")
    def clear_cart(self, request):
        membro = self._membro(request)
        cart = get_or_create_cart(membro)
        cart.items.all().delete()
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        membro = self._membro(request)
        ser = CheckoutSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        method = ser.validated_data.get("payment_method", "simulated")
        payment_method = (
            PaymentMethod.SIMULATED if method == "simulated" else PaymentMethod.MANUAL
        )
        auto_pay = method == "simulated"
        try:
            order = create_order_from_cart(
                membro,
                payment_method=payment_method,
                notes=ser.validated_data.get("notes", ""),
                auto_pay=auto_pay,
                user=request.user,
            )
        except DjangoValidationError as exc:
            msg = exc.messages[0] if hasattr(exc, "messages") else str(exc)
            raise ValidationError({"detail": msg})
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class PublicCatalogView(APIView):
    """GET /api/ecommerce/public/catalog/?schema= — vitrine pública (anuidades)."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        tenant = resolve_tenant_from_request(request)
        if not tenant:
            return Response(
                {"detail": "Informe ?schema= ou acesse via domínio do tenant."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item_type = request.query_params.get("item_type", CatalogItemType.ANUIDADE)
        with schema_context(tenant.schema_name):
            qs = CatalogItem.objects.filter(is_active=True)
            if item_type:
                qs = qs.filter(item_type=item_type)
            qs = qs.order_by("price", "name")[:50]
            return Response(
                {
                    "schema": tenant.schema_name,
                    "items": PublicCatalogItemSerializer(qs, many=True).data,
                }
            )


class EcommerceResumoView(APIView):
    """KPIs rápidos para dashboard da diretoria."""

    permission_classes = [IsAuthenticated, IsBoardOrAdmin]

    def get(self, request):
        return Response(
            {
                "itens_ativos": CatalogItem.objects.filter(is_active=True).count(),
                "pedidos_pendentes": Order.objects.filter(status=OrderStatus.PENDING).count(),
                "pedidos_pagos_mes": Order.objects.filter(
                    status__in=[OrderStatus.PAID, OrderStatus.FULFILLED]
                ).count(),
            }
        )
