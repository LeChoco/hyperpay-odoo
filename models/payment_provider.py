# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

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
