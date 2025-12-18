from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date
from decimal import Decimal

from apps.properties.models import Property
from .models import PaymentCategory, Transaction

class BillingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testadmin', password='password')
        self.client.force_authenticate(user=self.user)
        
        # Setup Categories
        self.income_cat = PaymentCategory.objects.create(name='Expensas', type='income')
        self.expense_cat = PaymentCategory.objects.create(name='Mantenimiento', type='expense')
        
        # Setup Property
        self.prop1 = Property.objects.create(house_number='101', block='A', area_m2=100)
        self.prop2 = Property.objects.create(house_number='102', block='A', area_m2=100)

    def test_create_income_transaction(self):
        """Probar creación de cobro individual"""
        data = {
            'transaction_type': 'income',
            'category': self.income_cat.id,
            'property': self.prop1.id,
            'amount': '500.00',
            'concept': 'Cobro Enero'
        }
        response = self.client.post(reverse('transaction-list'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(Transaction.objects.first().amount, Decimal('500.00'))

    def test_validation_income_needs_property(self):
        """Probar que un Ingreso requiere propiedad"""
        data = {
            'transaction_type': 'income',
            'category': self.income_cat.id,
            'amount': '500.00',
            'concept': 'Cobro sin casa'
        }
        response = self.client.post(reverse('transaction-list'), data)
        # DRF podría devolver 400 Bad Request por la validación del serializer que llama model.clean()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_batch_create_transactions(self):
        """Probar creación masiva para todas las propiedades"""
        url = reverse('transaction-batch-create')
        data = {
            'category': self.income_cat.id,
            'amount': '1000.00',
            'concept': 'Expensa General',
            'due_date': str(date.today())
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Debería haber 2 transacciones (prop1 y prop2)
        self.assertEqual(Transaction.objects.count(), 2)
        self.assertTrue(Transaction.objects.filter(property=self.prop1).exists())
        self.assertTrue(Transaction.objects.filter(property=self.prop2).exists())

    def test_stats_and_balance(self):
        """Probar endpoint de estadísticas"""
        # 1. Crear Ingreso (Cobro) de 1000
        Transaction.objects.create(
            transaction_type='income',
            category=self.income_cat,
            property=self.prop1,
            amount=1000,
            concept='Ingreso 1',
            status='pending'
        )
        
        # 2. Crear Egreso (Pago) de 300
        Transaction.objects.create(
            transaction_type='expense',
            category=self.expense_cat,
            amount=300,
            concept='Pago Jardinero',
            status='paid' # Estado irrelevante para suma total de egresos según lógica simple
        )
        
        url = reverse('transaction-stats')
        response = self.client.get(url)
        
        expected_data = {
            'total_income': 1000.0, # DRF decimal puede venir como float/string en test response JSON
            'total_expense': 300.0,
            'balance': 700.0,
            'pending_incomes_count': 1
        }
        
        # Convertir response data a float para comparar fácilmente
        self.assertEqual(float(response.data['total_income']), expected_data['total_income'])
        self.assertEqual(float(response.data['total_expense']), expected_data['total_expense'])
        self.assertEqual(float(response.data['balance']), expected_data['balance'])
        self.assertEqual(response.data['pending_incomes_count'], expected_data['pending_incomes_count'])
