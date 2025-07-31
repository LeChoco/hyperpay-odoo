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

    @api.model
    def _hyperpay_get_tx_from_notification_data(self, notification_data):
        """ Find the transaction based on the notification data.

        :param dict notification_data: The notification data
        :return: The transaction
        :rtype: recordset of `payment.transaction`
        """
        reference = notification_data.get('reference') or notification_data.get('merchantTransactionId')
        if not reference:
            raise ValidationError(
                "Hyperpay: " + _("Received notification with missing reference.")
            )

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'hyperpay')])
        if not tx:
            raise ValidationError(
                "Hyperpay: " + _("No transaction found for reference %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """ Process the transaction based on Hyperpay data.
        
        :param dict notification_data: The notification data
        """
        if self.provider_code != 'hyperpay':
            return super()._process_notification_data(notification_data)

        resource_path = notification_data.get('resourcePath')
        if resource_path:
            payment_status = self._hyperpay_get_payment_status(resource_path)
            self._hyperpay_handle_payment_status(payment_status)
        else:
            # Direct webhook notification, data is the payment status
            self._hyperpay_handle_payment_status(notification_data)

    def _hyperpay_get_payment_status(self, resource_path):
        """ Get the payment status from Hyperpay API.
        
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
        return self.provider_id._hyperpay_make_request(
            resource_path.lstrip('/'),
            payload=params,
            method='GET'
        )

    def _hyperpay_handle_payment_status(self, payment_status):
        """ Handle the payment status response from Hyperpay.
        
        :param dict payment_status: The payment status response
        """
        self.ensure_one()
        
        _logger.info("Hyperpay payment status response:\n%s", pprint.pformat(payment_status))
        
        # Extract the result information
        result = payment_status.get('result', {})
        result_code = result.get('code')

        if not result_code:
            raise ValidationError("Hyperpay: Received notification with no result code.")

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
        help="The payment ID returned by Hyperpay"
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