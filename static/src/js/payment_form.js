/** @odoo-module **/

import { PaymentForm } from "@payment/js/payment_form";

PaymentForm.include({
    /**
     * @override
     */
    async _processPayment(processingValues) {
        if (this.provider.code !== 'hyperpay') {
            return super._processPayment(processingValues);
        }

        // For Hyperpay, we redirect to their payment page
        const checkoutId = processingValues.checkout_id;
        const baseUrl = processingValues.base_url;
        const integrity = processingValues.integrity;
        const shopperResultUrl = processingValues.shopper_result_url;

        // Create the payment widget
        this._createHyperpayWidget(checkoutId, baseUrl, integrity, shopperResultUrl);
    },

    /**
     * Create the Hyperpay payment widget.
     * @param {string} checkoutId - The checkout ID from Hyperpay
     * @param {string} baseUrl - The base URL for Hyperpay
     * @param {string} integrity - The integrity key
     * @param {string} shopperResultUrl - The return URL
     */
    _createHyperpayWidget(checkoutId, baseUrl, integrity, shopperResultUrl) {
        // Load the Hyperpay payment widget script
        const script = document.createElement('script');
        script.src = `${baseUrl}/v1/paymentWidgets.js?checkoutId=${checkoutId}`;
        script.integrity = integrity;
        script.crossOrigin = 'anonymous';
        
        script.onload = () => {
            // Create the payment form
            const form = document.createElement('form');
            form.action = shopperResultUrl;
            form.className = 'paymentWidgets';
            form.setAttribute('data-brands', 'VISA MASTER AMEX');
            
            // Add the form to the payment container
            const container = this.el.querySelector('.payment_form');
            if (container) {
                container.appendChild(form);
            }
        };
        
        document.head.appendChild(script);
    },

    /**
     * Handle payment completion
     * @param {Object} result - The payment result
     */
    _handlePaymentCompletion(result) {
        console.log('Hyperpay payment completed:', result);
        
        // Redirect to the return URL
        if (result.redirectUrl) {
            window.location.href = result.redirectUrl;
        }
    }
}); 