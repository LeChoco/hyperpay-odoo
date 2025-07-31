# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
from urllib.parse import urljoin

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    #=== BUSINESS METHODS ===#

    def _get_specific_api_values(self, processing_values):
        """ Override of `payment` to return Hyperpay-specific API values.
        
        Note: self.ensure_one() from base method
        :param dict processing_values: The processing values of the transaction
        :return: The API values
        :rtype: dict
        """
        res = super()._get_specific_api_values(processing_values)
        if self.provider_code != 'hyperpay':
            return res

        return {
            'checkout_id': processing_values['checkout_id'],
            'base_url': processing_values['base_url'],
            'integrity': processing_values['integrity'],
            'shopper_result_url': processing_values['shopper_result_url'],
        }

    def _process_feedback_data(self, data):
        """ Override of `payment` to process the transaction based on Hyperpay data.
        
        Note: self.ensure_one() from base method
        :param dict data: The feedback data
        """
        super()._process_feedback_data(data)
        if self.provider_code != 'hyperpay':
            return

        # Extract the resource path from the data
        resource_path = data.get('resourcePath')
        if not resource_path:
            raise ValidationError(_("Hyperpay: received data with missing resourcePath"))

        # Get the payment status from Hyperpay (using COPYandPAY method)
        payment_status = self._copyandpay_get_payment_status(resource_path)
        
        # Update the transaction based on the payment status
        self._handle_copyandpay_payment_status(payment_status)

    def _copyandpay_get_payment_status(self, resource_path):
        """ Get the payment status from Hyperpay API (using COPYandPAY method).
        
        :param str resource_path: The resource path from the callback
        :return: The payment status response
        :rtype: dict
        """
        self.ensure_one()
        
        # Prepare the request parameters
        params = {
            'entityId': self.provider_id.hyperpay_entity_id,
        }
        
        # Make the request to get payment status
        return self.provider_id._copyandpay_make_request(
            resource_path.lstrip('/'), 
            payload=params, 
            method='GET'
        )

    def _handle_copyandpay_payment_status(self, payment_status):
        """ Handle the payment status response from Hyperpay (using COPYandPAY method).
        
        :param dict payment_status: The payment status response
        """
        self.ensure_one()
        
        _logger.info("Hyperpay payment status response:\n%s", pprint.pformat(payment_status))
        
        # Extract the result information
        result = payment_status.get('result', {})
        result_code = result.get('code')
        result_description = result.get('description', '')
        
        # Map Hyperpay result codes to Odoo transaction states
        if result_code == '000.100.110':  # Success
            self._set_done()
            self._log_received_acknowledgement()
        elif result_code in ['800.400.500', '800.400.501', '800.400.502']:  # Pending
            self._set_pending()
        elif result_code in ['800.400.503', '800.400.504', '800.400.505']:  # Failed
            self._set_canceled()
        else:
            # Unknown status, set as pending and log
            _logger.warning("Hyperpay: unknown result code %s: %s", result_code, result_description)
            self._set_pending()

        # Store additional information
        self.write({
            'hyperpay_payment_id': payment_status.get('id'),
            'hyperpay_brand': payment_status.get('paymentBrand'),
            'hyperpay_type': payment_status.get('paymentType'),
        })

    def _log_received_acknowledgement(self):
        """ Log the received acknowledgement for the transaction.
        
        Note: self.ensure_one()
        """
        self.ensure_one()
        _logger.info(
            "received data with status %(status)s for transaction with reference %(ref)s",
            {'status': self.state, 'ref': self.reference}
        )

    #=== FIELDS ===#

    hyperpay_payment_id = fields.Char(
        string="Hyperpay Payment ID",
        readonly=True,
        help="The payment ID returned by Hyperpay (COPYandPAY method)"
    )
    hyperpay_brand = fields.Char(
        string="Hyperpay Brand",
        readonly=True,
        help="The payment brand (VISA, MASTER, etc.)"
    )
    hyperpay_type = fields.Char(
        string="Hyperpay Type",
        readonly=True,
        help="The payment type (DB, PA, etc.)"
    ) 