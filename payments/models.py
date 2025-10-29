from django.db import models
from django.conf import settings
from django.utils import timezone

class MpesaTransaction(models.Model):
    """Model to store M-Pesa transaction details"""
    TRANSACTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mpesa_transactions'
    )
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account_reference = models.CharField(max_length=50)
    transaction_desc = models.CharField(max_length=100, default='Payment')
    merchant_request_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True, unique=True, db_index=True)
    mpesa_receipt_number = models.CharField(max_length=100, blank=True, null=True)
    transaction_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=TRANSACTION_STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    result_code = models.CharField(max_length=10, blank=True, null=True)
    result_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.phone_number} - {self.amount} - {self.status}"

    def is_successful(self):
        return self.status == 'completed' and self.mpesa_receipt_number is not None

    class Meta:
        ordering = ['-created_at']
