# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# NOTE: Imports for 'json', 'logging', 'requests', 'urllib.parse' have been removed
# as a debugging measure to ensure they are not causing a silent failure during module loading.

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('hyperpay', "Hyperpay")], 
        ondelete={'hyperpay': 'set default'}
    )

    hyperpay_entity_id = fields.Char(string="Entity ID")
    hyperpay_access_token = fields.Char(string="Access Token", groups='base.group_system')
    hyperpay_base_url = fields.Char(string="Base URL", default="https://eu-test.oppwa.com/")
    hyperpay_integrity_key = fields.Char(string="Integrity Key", groups='base.group_system')

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'hyperpay').update({
            'support_express_checkout': False,
            'support_manual_capture': 'full_only',
            'support_refund': 'partial',
            'support_tokenization': False,
        })

    def _get_specific_rendering_values(self, transaction):
        """ Override of `payment` to return Hyperpay-specific rendering values.

        Note: self.ensure_one() from base method
        """
        # This method is temporarily disabled for debugging.
        # It requires 'requests' and 'urllib' which have been removed.
        res = super()._get_specific_rendering_values(transaction)
        if self.code != 'hyperpay':
            return res
        # The actual logic is commented out to prevent import errors.
        # ...
        return res

    def _get_return_url(self, transaction):
        """ Return the URL where the customer should be redirected after payment. """
        # This method is temporarily disabled for debugging.
        # It requires 'urllib.parse' which has been removed.
        # from urllib.parse import urljoin
        # return urljoin(self.get_base_url(), f'/payment/hyperpay/return?reference={transaction.reference}')
        return ''

    def _get_webhook_url(self):
        """ Return the webhook URL for Hyperpay notifications. """
        # This method is temporarily disabled for debugging.
        # It requires 'urllib.parse' which has been removed.
        # from urllib.parse import urljoin
        # return urljoin(self.get_base_url(), '/payment/hyperpay/webhook')
        return ''
