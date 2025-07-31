# Hyperpay Payment Provider for Odoo 17.2

This module integrates Hyperpay payment service with Odoo 17.2 (using COPYandPAY method), allowing merchants to accept payments through the Hyperpay platform.

## Features

- **Payment Processing**: Process payments through Hyperpay API (using COPYandPAY method)
- **Webhook Support**: Handle server-to-server notifications
- **Payment Status Tracking**: Track payment status and update orders
- **Multiple Payment Methods**: Support for VISA, MasterCard, and American Express
- **Secure Integration**: Uses Hyperpay's secure payment widgets (COPYandPAY method)

## Installation

1. Copy the `payment_hyperpay` module to your Odoo addons directory
2. Update the addons list in Odoo
3. Install the "Payment Provider: Hyperpay" module
4. Configure the payment provider settings

## Configuration

### 1. Payment Provider Setup

1. Go to **Accounting > Configuration > Payment Providers**
2. Create a new payment provider or edit the existing Hyperpay provider
3. Configure the following settings:

#### Required Fields:
- **Entity ID**: Your Hyperpay entity ID (e.g., `8ac7a4c79394bdc801939736f17e063d`)
- **Access Token**: Your Hyperpay access token
- **Base URL**: 
  - Test: `https://eu-test.oppwa.com/`
  - Production: `https://eu-prod.oppwa.com/`

#### Optional Fields:
- **Integrity Key**: For additional security validation

### 2. Webhook Configuration

Configure the webhook URL in your Hyperpay merchant portal:
```
https://your-odoo-domain.com/payment/hyperpay/webhook
```

### 3. Return URL Configuration

The return URL is automatically configured as:
```
https://your-odoo-domain.com/payment/hyperpay/return
```

## API Integration

### Step 1: Create Checkout Session

The module automatically creates a checkout session when a payment is initiated:

```python
# Example checkout request
checkout_data = {
    'entityId': '8ac7a4c79394bdc801939736f17e063d',
    'amount': '92.00',
    'currency': 'EUR',
    'paymentType': 'DB',
    'integrity': 'true',
    'merchantTransactionId': transaction.reference,
    'customer.email': 'customer@example.com',
    'customer.givenName': 'John',
    'customer.surname': 'Doe',
}
```

### Step 2: Payment Form

The payment form is automatically generated with the Hyperpay widget (using COPYandPAY method):

```html
<script src="https://eu-test.oppwa.com/v1/paymentWidgets.js?checkoutId={checkoutId}" 
        integrity="{integrity}" 
        crossorigin="anonymous">
</script>
<form action="{shopperResultUrl}" class="paymentWidgets" data-brands="VISA MASTER AMEX">
</form>
```

### Step 3: Payment Status Check

After payment completion, the module checks the payment status:

```python
# Example status check
params = {
    'entityId': '8ac7a4c79394bdc801939736f17e063d',
}
response = provider._copyandpay_make_request(
    'v1/checkouts/{checkoutId}/payment', 
    payload=params, 
    method='GET'
)
```

## Payment Flow

1. **Customer initiates payment** on your website
2. **Odoo creates transaction** and generates checkout session
3. **Customer is redirected** to Hyperpay payment page
4. **Customer completes payment** on Hyperpay
5. **Hyperpay redirects** customer back to your site
6. **Odoo processes callback** and updates transaction status
7. **Order is marked as paid** if payment is successful

## Transaction States

The module maps Hyperpay result codes to Odoo transaction states:

- **Success** (`000.100.110`): Transaction marked as `done`
- **Pending** (`800.400.500`, `800.400.501`, `800.400.502`): Transaction marked as `pending`
- **Failed** (`800.400.503`, `800.400.504`, `800.400.505`): Transaction marked as `cancel`

## API Endpoints

### Return URL
```
GET /payment/hyperpay/return
```
Handles customer redirect after payment completion.

### Webhook URL
```
POST /payment/hyperpay/webhook
```
Handles server-to-server notifications from Hyperpay.

### Status Check URL
```
GET /payment/hyperpay/status
```
Manual status check endpoint (for debugging).

## Error Handling

The module includes comprehensive error handling:

- **API Communication Errors**: Logged and user-friendly messages displayed
- **Invalid Transaction References**: Proper validation and error responses
- **Webhook Processing Errors**: Secure error handling with appropriate HTTP status codes

## Security Features

- **CSRF Protection**: Disabled for webhook endpoints as required
- **Authentication**: Bearer token authentication for API calls
- **Integrity Validation**: Optional integrity key validation
- **Secure Redirects**: Proper URL validation and sanitization

## Testing

### Test Environment
- Use the test base URL: `https://eu-test.oppwa.com/`
- Use test entity ID and access token
- Test with small amounts

### Production Environment
- Use the production base URL: `https://eu-prod.oppwa.com/`
- Use production entity ID and access token
- Ensure webhook is properly configured

## Troubleshooting

### Common Issues

1. **Payment not processing**: Check entity ID and access token
2. **Webhook not receiving**: Verify webhook URL configuration
3. **Transaction not updating**: Check payment status API calls
4. **Form not loading**: Verify integrity key and checkout ID

### Logs

Check Odoo logs for detailed error messages:
```bash
tail -f /var/log/odoo/odoo.log | grep hyperpay
```

## Support

For issues with this module, please check:
1. Hyperpay API documentation (COPYandPAY method)
2. Odoo payment module documentation
3. Module logs for specific error messages

## License

This module is licensed under LGPL-3.

## Version History

- **1.0**: Initial release with basic payment processing
- Support for VISA, MasterCard, and American Express
- Webhook integration
- Payment status tracking 