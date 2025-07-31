# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint
from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class HyperpayController(http.Controller):
    _return_url = '/payment/hyperpay/return'
    _webhook_url = '/payment/hyperpay/webhook'

    @http.route(_return_url, type='http', methods=['GET'], auth='public')
    def hyperpay_return(self, **data):
        """ Process the notification data sent by Hyperpay after redirection from payment.
        
        :param dict data: The notification data, including the reference appended to the URL
        """
        _logger.info("Hyperpay return with data:\n%s", pprint.pformat(data))
        
        # Retrieve the transaction and handle the notification data
        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('hyperpay', data)
        tx_sudo._handle_notification_data(data)
        
        # Redirect the user to the status page
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', methods=['POST'], auth='public', csrf=False)
    def hyperpay_webhook(self):
        """ Process the notification data sent by Hyperpay to the webhook.
        
        :return: An empty string to acknowledge the notification
        :rtype: str
        """
        data = request.get_json_data()
        _logger.info("Hyperpay webhook received with data:\n%s", pprint.pformat(data))
        
        try:
            # Retrieve the transaction and handle the notification data
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('hyperpay', data)
            tx_sudo._handle_notification_data(data)
            return 'OK'
        except ValidationError:
            _logger.exception("Could not retrieve transaction for Hyperpay notification.")
            raise Forbidden()

    @http.route('/payment/hyperpay/status', type='http', methods=['GET'], auth='public')
    def hyperpay_status(self, **data):
        """ Handle status check requests from Hyperpay.
        
        This route can be used to check the status of a payment manually.
        
        :param dict data: The status check data
        :return: JSON response with payment status
        """
        _logger.info("Hyperpay status check with data:\n%s", pprint.pformat(data))
        
        try:
            reference = data.get('reference')
            if not reference:
                return {'error': 'Missing reference parameter'}
            
            # Retrieve the transaction
            tx_sudo = request.env['payment.transaction'].sudo().search([
                ('reference', '=', reference),
                ('provider_code', '=', 'hyperpay')
            ], limit=1)
            
            if not tx_sudo:
                return {'error': 'Transaction not found'}
            
            # Return the transaction status
            return {
                'reference': tx_sudo.reference,
                'status': tx_sudo.state,
                'amount': tx_sudo.amount,
                'currency': tx_sudo.currency_id.name,
                'hyperpay_payment_id': tx_sudo.hyperpay_payment_id,
                'hyperpay_brand': tx_sudo.hyperpay_brand,
                'hyperpay_type': tx_sudo.hyperpay_type,
            }
            
        except Exception as error:
            _logger.error("Hyperpay status check failed: %s", error)
            return {'error': str(error)} 