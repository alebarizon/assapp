"""Views financeiras AssApp — scoping por schema do tenant."""
from calendar import monthrange
from datetime import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mandatos.models import Mandato
from mandatos.permissions import IsBoardOrAdmin

from .models import ExpenseCategory, IncomeCategory, Transaction, TransactionType
from .serializers import TransactionSerializer


MONTH_NAMES = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}


def _period_bounds(month: int, year: int):
    tz = timezone.get_current_timezone()
    first_day = datetime(year, month, 1, tzinfo=tz)
    last_n = monthrange(year, month)[1]
    last_day = datetime(year, month, last_n, 23, 59, 59, tzinfo=tz)
    return first_day, last_day


def _period_queryset(month: int, year: int):
    first_day, last_day = _period_bounds(month, year)
    return Transaction.objects.filter(occurred_at__gte=first_day, occurred_at__lte=last_day)


def _parse_month_year(request):
    now = timezone.now()
    try:
        month = int(request.query_params.get("month") or request.data.get("month") or now.month)
        year = int(request.query_params.get("year") or request.data.get("year") or now.year)
    except (TypeError, ValueError):
        month, year = now.month, now.year
    if month < 1 or month > 12:
        month = now.month
    if year < 2000 or year > 2100:
        year = now.year
    return month, year


def _build_summary(month: int, year: int) -> dict:
    qs = _period_queryset(month, year)
    first_day, last_day = _period_bounds(month, year)
    total_income = qs.filter(type=TransactionType.INCOME).aggregate(t=Sum("amount"))["t"] or 0
    total_expense = qs.filter(type=TransactionType.EXPENSE).aggregate(t=Sum("amount"))["t"] or 0
    balance = total_income - total_expense

    income_by_category = {}
    for code, name in IncomeCategory.choices:
        total = (
            qs.filter(type=TransactionType.INCOME, category=code).aggregate(t=Sum("amount"))["t"]
            or 0
        )
        if total > 0:
            income_by_category[code] = {"name": name, "amount": str(total)}

    expense_by_category = {}
    for code, name in ExpenseCategory.choices:
        total = (
            qs.filter(type=TransactionType.EXPENSE, category=code).aggregate(t=Sum("amount"))["t"]
            or 0
        )
        if total > 0:
            expense_by_category[code] = {"name": name, "amount": str(total)}

    return {
        "period": {
            "month": month,
            "year": year,
            "month_name": MONTH_NAMES.get(month, ""),
            "start_date": first_day.isoformat(),
            "end_date": last_day.isoformat(),
        },
        "total_income": str(total_income),
        "total_expense": str(total_expense),
        "balance": str(balance),
        "is_negative": balance < 0,
        "income_by_category": income_by_category,
        "expense_by_category": expense_by_category,
        "transactions_count": qs.count(),
        "generated_at": timezone.now().isoformat(),
    }


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]

    def get_queryset(self):
        qs = Transaction.objects.select_related("user", "mandato").all()
        tx_type = self.request.query_params.get("type")
        category = self.request.query_params.get("category")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        if tx_type:
            qs = qs.filter(type=tx_type)
        if category:
            qs = qs.filter(category=category)
        if start_date:
            qs = qs.filter(occurred_at__gte=start_date)
        if end_date:
            qs = qs.filter(occurred_at__lte=end_date)
        return qs.order_by("-occurred_at", "-created_at")

    def perform_create(self, serializer):
        mandato = Mandato.get_ativo()
        serializer.save(user=self.request.user, mandato=mandato)


class FinancialDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]

    def get(self, request):
        month, year = _parse_month_year(request)
        data = _build_summary(month, year)
        return Response(
            {
                "period": data["period"],
                "total_income": data["total_income"],
                "total_expense": data["total_expense"],
                "balance": data["balance"],
                "is_negative": data["is_negative"],
                "generated_at": data["generated_at"],
            }
        )


class MonthlyReportView(APIView):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]

    def get(self, request):
        month, year = _parse_month_year(request)
        return Response(_build_summary(month, year))


class SendReportEmailView(APIView):
    permission_classes = [IsAuthenticated, IsBoardOrAdmin]

    def post(self, request):
        month, year = _parse_month_year(request)
        recipient = (request.data.get("recipient_email") or request.user.email or "").strip()
        if not recipient or "@" not in recipient:
            return Response({"detail": "Email inválido."}, status=status.HTTP_400_BAD_REQUEST)

        data = _build_summary(month, year)
        month_name = data["period"]["month_name"]
        subject = f"Relatório Financeiro AssApp — {month_name}/{year}"

        income_lines = "".join(
            f"<li>{v['name']}: R$ {v['amount']}</li>" for v in data["income_by_category"].values()
        )
        expense_lines = "".join(
            f"<li>{v['name']}: R$ {v['amount']}</li>" for v in data["expense_by_category"].values()
        )
        html = f"""
        <html><body style="font-family:Arial,sans-serif;padding:20px;">
        <h2>{subject}</h2>
        <ul>
          <li><strong>Receitas:</strong> R$ {data['total_income']}</li>
          <li><strong>Despesas:</strong> R$ {data['total_expense']}</li>
          <li><strong>Saldo:</strong> R$ {data['balance']}</li>
        </ul>
        <h3>Receitas por categoria</h3><ul>{income_lines or '<li>—</li>'}</ul>
        <h3>Despesas por categoria</h3><ul>{expense_lines or '<li>—</li>'}</ul>
        <p>Total de lançamentos: {data['transactions_count']}</p>
        </body></html>
        """
        text = (
            f"{subject}\nReceitas: {data['total_income']}\n"
            f"Despesas: {data['total_expense']}\nSaldo: {data['balance']}"
        )
        try:
            send_mail(
                subject=subject,
                message=text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                html_message=html,
                fail_silently=False,
            )
        except Exception as exc:
            return Response(
                {
                    "detail": "Erro ao enviar e-mail. Verifique SMTP.",
                    "error": str(exc),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"detail": "Relatório enviado.", "recipient": recipient})


class CategoriesView(APIView):
    """Lista categorias OSC para o frontend."""

    permission_classes = [IsAuthenticated, IsBoardOrAdmin]

    def get(self, request):
        return Response(
            {
                "income": [{"value": c.value, "label": c.label} for c in IncomeCategory],
                "expense": [{"value": c.value, "label": c.label} for c in ExpenseCategory],
            }
        )
