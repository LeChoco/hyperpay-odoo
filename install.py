#!/usr/bin/env python3
"""
Hyperpay Payment Provider Installation Script

This script helps set up the Hyperpay payment provider in Odoo (using COPYandPAY method).
Run this script after installing the module to configure the payment provider.
"""

import logging
import sys
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def install_hyperpay_provider(env):
    """Install and configure the Hyperpay payment provider."""
    
    try:
        # Check if the module is installed
        module = env['ir.module.module'].search([('name', '=', 'payment_hyperpay')])
        if not module or module.state != 'installed':
            _logger.error("Hyperpay payment module is not installed. Please install it first.")
            return False
        
        # Create or update the payment provider
        provider = env['payment.provider'].search([('code', '=', 'hyperpay')], limit=1)
        
        if not provider:
            # Create new provider
            provider = env['payment.provider'].create({
                'name': 'Hyperpay',
                'code': 'hyperpay',
                'state': 'test',  # Start in test mode
                'company_id': env.ref('base.main_company').id,
                'hyperpay_entity_id': '8ac7a4c79394bdc801939736f17e063d',  # Test entity ID
                'hyperpay_access_token': 'OGFjN2E0Yzc5Mzk0YmRjODAxOTM5NzM2ZjFhNzA2NDF8enlac1lYckc4QXk6bjYzI1NHNng=',  # Test token
                'hyperpay_base_url': 'https://eu-test.oppwa.com/',
                'sequence': 10,
            })
            _logger.info("Created new Hyperpay payment provider")
        else:
            _logger.info("Hyperpay payment provider already exists")
        
        # Update provider settings
        provider.write({
            'hyperpay_entity_id': '8ac7a4c79394bdc801939736f17e063d',
            'hyperpay_access_token': 'OGFjN2E0Yzc5Mzk0YmRjODAxOTM5NzM2ZjFhNzA2NDF8enlac1lYckc4QXk6bjYzI1NHNng=',
            'hyperpay_base_url': 'https://eu-test.oppwa.com/',
        })
        
        _logger.info("Hyperpay payment provider configured successfully")
        _logger.info("Provider ID: %s", provider.id)
        _logger.info("Test Entity ID: %s", provider.hyperpay_entity_id)
        _logger.info("Test Base URL: %s", provider.hyperpay_base_url)
        
        return True
        
    except Exception as e:
        _logger.error("Failed to install Hyperpay provider: %s", str(e))
        return False


def main():
    """Main installation function."""
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    _logger.info("Starting Hyperpay payment provider installation...")
    
    try:
        # Initialize Odoo environment
        from odoo.cli.server import main as odoo_main
        from odoo import api, SUPERUSER_ID
        
        # Create environment
        env = api.Environment.manage()
        with env.manage():
            # Run installation
            success = install_hyperpay_provider(env)
            
            if success:
                _logger.info("Hyperpay payment provider installation completed successfully!")
                _logger.info("Next steps:")
                _logger.info("1. Go to Accounting > Configuration > Payment Providers")
                _logger.info("2. Edit the Hyperpay provider")
                _logger.info("3. Update with your production credentials")
                _logger.info("4. Set state to 'enabled' for production use")
            else:
                _logger.error("Hyperpay payment provider installation failed!")
                sys.exit(1)
                
    except Exception as e:
        _logger.error("Installation failed: %s", str(e))
        sys.exit(1)


if __name__ == '__main__':
    main() 