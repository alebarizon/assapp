from rest_framework import serializers

from .models import ExpenseCategory, IncomeCategory, Transaction, TransactionType


class TransactionSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True, allow_null=True)
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    category_display = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = (
            "id",
            "user",
            "user_email",
            "mandato",
            "description",
            "amount",
            "type",
            "type_display",
            "category",
            "category_display",
            "occurred_at",
            "referencia",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "referencia", "created_at", "updated_at")

    def get_category_display(self, obj):
        if obj.type == TransactionType.INCOME:
            return dict(IncomeCategory.choices).get(obj.category, obj.category)
        return dict(ExpenseCategory.choices).get(obj.category, obj.category)

    def validate(self, data):
        tx_type = data.get("type") or getattr(self.instance, "type", None)
        category = data.get("category") or getattr(self.instance, "category", None)
        amount = data.get("amount", getattr(self.instance, "amount", None))

        if amount is not None and amount <= 0:
            raise serializers.ValidationError({"amount": "O valor deve ser maior que zero."})

        if tx_type == TransactionType.INCOME:
            valid = {c.value for c in IncomeCategory}
        elif tx_type == TransactionType.EXPENSE:
            valid = {c.value for c in ExpenseCategory}
        else:
            valid = set()
        if category and category not in valid:
            raise serializers.ValidationError({"category": "Categoria inválida para o tipo."})
        return data
