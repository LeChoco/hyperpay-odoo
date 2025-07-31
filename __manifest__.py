# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payment Provider: Hyperpay',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'sequence': 350,
    'summary': "A payment provider for Hyperpay integration using COPYandPAY method.",
    'description': " ",
    'depends': ['payment', 'web', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_provider_views.xml',
        'views/payment_hyperpay_templates.xml',
        'data/payment_provider_data.xml',
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_hyperpay/static/src/**/*',
        ],
    },
    'license': 'LGPL-3',
} 
