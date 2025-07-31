# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json
import logging
import requests
from urllib.parse import urljoin

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('hyperpay', "Hyperpay")], 
        ondelete={'hyperpay': 'set default'}
    )
    
    # Hyperpay specific fields (using COPYandPAY method)
    hyperpay_entity_id = fields.Char(string="Entity ID")
    hyperpay_access_token = fields.Char(string="Access Token", groups='base.group_system')
    hyperpay_base_url = fields.Char(string="Base URL", default="https://eu-test.oppwa.com/")
    hyperpay_integrity_key = fields.Char(string="Integrity Key", groups='base.group_system')

    #=== COMPUTE METHODS ===#

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'hyperpay').update({
            'support_express_checkout': False,
            'support_manual_capture': 'full_only',
            'support_refund': 'partial',
            'support_tokenization': False,
        })

    #=== BUSINESS METHODS ===#

    def _hyperpay_make_request(self, endpoint, payload=None, method='POST'):
        """ Make a request to the Hyperpay API.

        :param str endpoint: The API endpoint to call
        :param dict payload: The payload to send
        :param str method: The HTTP method to use
        :return: The API response
        :rtype: dict
        """
        self.ensure_one()
        
        url = urljoin(self.hyperpay_base_url, endpoint)
        headers = {
            'Authorization': f'Bearer {self.hyperpay_access_token}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, params=payload, headers=headers, timeout=30)
            else:
                response = requests.post(url, data=payload, headers=headers, timeout=30)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as error:
            _logger.error("Hyperpay API request failed: %s", error)
            raise UserError(_("The communication with the payment provider failed. Please try again."))

    def _get_specific_rendering_values(self, transaction):
        """ Override of `payment` to return Hyperpay-specific rendering values.
        
        Note: self.ensure_one() from base method
        :param recordset transaction: The transaction for which rendering values are requested
        :return: The rendering values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(transaction)
        if self.code != 'hyperpay':
            return res

        # Prepare the checkout request
        checkout_data = {
            'entityId': self.hyperpay_entity_id,
            'amount': f"{transaction.amount:.2f}",
            'currency': transaction.currency_id.name,
            'paymentType': 'DB',  # Direct Debit
            'integrity': 'true',
            'merchantTransactionId': transaction.reference,
            'customer.email': transaction.partner_id.email,
            'customer.givenName': transaction.partner_id.first_name or transaction.partner_id.name,
            'customer.surname': transaction.partner_id.last_name or '',
        }

        # Make the checkout request
        checkout_response = self._hyperpay_make_request('v1/checkouts', checkout_data)
        
        if checkout_response.get('result', {}).get('code') != '000.200.000':
            error_msg = checkout_response.get('result', {}).get('description', 'Unknown error')
            raise UserError(_("Failed to create payment session: %s", error_msg))

        checkout_id = checkout_response.get('id')
        
        # Prepare the payment form values
        res.update({
            'checkout_id': checkout_id,
            'base_url': self.hyperpay_base_url.rstrip('/'),
            'integrity': self.hyperpay_integrity_key or '',
            'shopper_result_url': self._get_return_url(transaction),
        })
        
        return res

    def _get_return_url(self, transaction):
        """ Return the URL where the customer should be redirected after payment.
        
        :param recordset transaction: The transaction
        :return: The return URL
        :rtype: str
        """
        return urljoin(self.get_base_url(), f'/payment/hyperpay/return?reference={transaction.reference}')

    def _get_webhook_url(self):
        """ Return the webhook URL for Hyperpay notifications.
        
        :return: The webhook URL
        :rtype: str
        """
        return urljoin(self.get_base_url(), '/payment/hyperpay/webhook') 