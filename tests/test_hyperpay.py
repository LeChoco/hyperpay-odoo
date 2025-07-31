# Part of Odoo. See LICENSE file for full copyright and licensing details.

import unittest
from unittest.mock import patch, MagicMock

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestHyperpayPayment(TransactionCase):
    """Test Hyperpay payment provider functionality."""

    def setUp(self):
        super().setUp()
        
        # Create test company
        self.company = self.env['res.company'].create({
            'name': 'Test Company',
        })
        
        # Create test partner
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test@example.com',
        })
        
        # Create test currency
        self.currency = self.env['res.currency'].create({
            'name': 'EUR',
            'symbol': '€',
        })
        
        # Create Hyperpay payment provider
        self.provider = self.env['payment.provider'].create({
            'name': 'Hyperpay Test',
            'code': 'hyperpay',
            'state': 'test',
            'company_id': self.company.id,
            'hyperpay_entity_id': '8ac7a4c79394bdc801939736f17e063d',
            'hyperpay_access_token': 'OGFjN2E0Yzc5Mzk0YmRjODAxOTM5NzM2ZjFhNzA2NDF8enlac1lYckc4QXk6bjYzI1NHNng=',
            'hyperpay_base_url': 'https://eu-test.oppwa.com/',
        })

    def test_provider_creation(self):
        """Test that the payment provider is created correctly."""
        self.assertEqual(self.provider.code, 'hyperpay')
        self.assertEqual(self.provider.state, 'test')
        self.assertEqual(self.provider.hyperpay_entity_id, '8ac7a4c79394bdc801939736f17e063d')

    def test_provider_required_fields(self):
        """Test that required fields are enforced."""
        with self.assertRaises(UserError):
            self.provider.hyperpay_entity_id = False
            self.provider._check_required_fields()

    def test_get_tx_from_notification_data(self):
        """Test that the transaction can be found from notification data."""
        # Create a test transaction
        transaction = self.env['payment.transaction'].create({
            'reference': 'TEST_REF_002',
            'amount': 100.0,
            'currency_id': self.currency.id,
            'partner_id': self.partner.id,
            'provider_id': self.provider.id,
        })

        # Test with reference
        data_with_ref = {'reference': 'TEST_REF_002'}
        tx = self.env['payment.transaction']._hyperpay_get_tx_from_notification_data(data_with_ref)
        self.assertEqual(tx, transaction)

        # Test with merchantTransactionId
        data_with_merch_id = {'merchantTransactionId': 'TEST_REF_002'}
        tx = self.env['payment.transaction']._hyperpay_get_tx_from_notification_data(data_with_merch_id)
        self.assertEqual(tx, transaction)

        # Test with missing reference
        with self.assertRaises(ValidationError):
            self.env['payment.transaction']._hyperpay_get_tx_from_notification_data({})

        # Test with non-existing reference
        with self.assertRaises(ValidationError):
            self.env['payment.transaction']._hyperpay_get_tx_from_notification_data({'reference': 'FAKE_REF'})

    @patch('odoo.addons.payment_hyperpay.models.payment_provider.requests.post')
    def test_make_request_success(self, mock_post):
        """Test successful API request."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'result': {
                'code': '000.200.000',
                'description': 'Success'
            },
            'id': 'test_checkout_id'
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        result = self.provider._hyperpay_make_request('v1/checkouts', {'test': 'data'})
        
        self.assertEqual(result['result']['code'], '000.200.000')
        self.assertEqual(result['id'], 'test_checkout_id')

    @patch('odoo.addons.payment_hyperpay.models.payment_provider.requests.post')
    def test_make_request_failure(self, mock_post):
        """Test failed API request."""
        mock_post.side_effect = Exception('Connection error')
        
        with self.assertRaises(UserError):
            self.provider._hyperpay_make_request('v1/checkouts', {'test': 'data'})

    def test_get_specific_rendering_values(self):
        """Test rendering values generation."""
        # Create a test transaction
        transaction = self.env['payment.transaction'].create({
            'reference': 'TEST_REF_001',
            'amount': 100.0,
            'currency_id': self.currency.id,
            'partner_id': self.partner.id,
            'provider_id': self.provider.id,
        })
        
        with patch.object(self.provider, '_hyperpay_make_request') as mock_request:
            mock_request.return_value = {
                'result': {'code': '000.200.000'},
                'id': 'test_checkout_id'
            }
            
            values = self.provider._get_specific_rendering_values(transaction)
            
            self.assertIn('checkout_id', values)
            self.assertIn('base_url', values)
            self.assertIn('shopper_result_url', values)

    def test_transaction_processing(self):
        """Test transaction processing with Hyperpay data."""
        # Create a test transaction
        transaction = self.env['payment.transaction'].create({
            'reference': 'TEST_REF_001',
            'amount': 100.0,
            'currency_id': self.currency.id,
            'partner_id': self.partner.id,
            'provider_id': self.provider.id,
        })
        
        # Test data with resourcePath
        test_data = {
            'resourcePath': '/v1/checkouts/test_id/payment'
        }
        
        with patch.object(transaction, '_hyperpay_get_payment_status') as mock_status:
            mock_status.return_value = {
                'result': {'code': '000.100.110'},
                'id': 'test_payment_id',
                'paymentBrand': 'VISA',
                'paymentType': 'DB'
            }
            
            transaction._handle_notification_data(test_data)
            
            self.assertEqual(transaction.state, 'done')
            self.assertEqual(transaction.hyperpay_payment_id, 'test_payment_id')
            self.assertEqual(transaction.hyperpay_brand, 'VISA')
            self.assertEqual(transaction.hyperpay_type, 'DB')

    def test_transaction_processing_missing_resource_path(self):
        """Test transaction processing with missing resourcePath."""
        transaction = self.env['payment.transaction'].create({
            'reference': 'TEST_REF_001',
            'amount': 100.0,
            'currency_id': self.currency.id,
            'partner_id': self.partner.id,
            'provider_id': self.provider.id,
        })
        
        test_data = {}  # Missing resourcePath
        
        with self.assertRaises(ValidationError):
            transaction._handle_notification_data(test_data)

    def test_payment_status_handling(self):
        """Test different payment status codes."""
        transaction = self.env['payment.transaction'].create({
            'reference': 'TEST_REF_001',
            'amount': 100.0,
            'currency_id': self.currency.id,
            'partner_id': self.partner.id,
            'provider_id': self.provider.id,
        })
        
        # Test success status
        success_status = {
            'result': {'code': '000.100.110'},
            'id': 'test_payment_id'
        }
        transaction._hyperpay_handle_payment_status(success_status)
        self.assertEqual(transaction.state, 'done')
        
        # Test pending status
        transaction.state = 'draft'  # Reset state
        pending_status = {
            'result': {'code': '800.400.500'},
            'id': 'test_payment_id'
        }
        transaction._hyperpay_handle_payment_status(pending_status)
        self.assertEqual(transaction.state, 'pending')
        
        # Test failed status
        transaction.state = 'draft'  # Reset state
        failed_status = {
            'result': {'code': '800.400.503'},
            'id': 'test_payment_id'
        }
        transaction._hyperpay_handle_payment_status(failed_status)
        self.assertEqual(transaction.state, 'cancel')

    def test_get_return_url(self):
        """Test return URL generation."""
        transaction = self.env['payment.transaction'].create({
            'reference': 'TEST_REF_001',
            'amount': 100.0,
            'currency_id': self.currency.id,
            'partner_id': self.partner.id,
            'provider_id': self.provider.id,
        })
        
        return_url = self.provider._get_return_url(transaction)
        self.assertIn('/payment/hyperpay/return', return_url)
        self.assertIn('reference=TEST_REF_001', return_url)

    def test_get_webhook_url(self):
        """Test webhook URL generation."""
        webhook_url = self.provider._get_webhook_url()
        self.assertIn('/payment/hyperpay/webhook', webhook_url)


if __name__ == '__main__':
    unittest.main() 