# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('hyperpay', "Hyperpay")], 
        ondelete={'hyperpay': 'set default'}
    )
