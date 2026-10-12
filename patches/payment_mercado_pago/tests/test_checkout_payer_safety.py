from unittest.mock import patch
from types import SimpleNamespace

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import MercadoPagoCommon
from ..controllers import payment as payment_controller


@tagged('post_install', '-at_install')
class TestCheckoutPayerSafety(MercadoPagoCommon):
    """Exercise the customized payer seam without any provider network calls."""

    def setUp(self):
        super().setUp()
        self.tx = self._create_transaction(flow='redirect')

    def _payer(self, code, number):
        identity = self.env['l10n_latam.identification.type'].with_context(active_test=False).search([
            ('l10n_pe_vat_code', '=', code),
        ], limit=1)
        if not identity:
            identity = self.env['l10n_latam.identification.type'].create({
                'name': 'Local test document', 'l10n_pe_vat_code': code,
            })
        return self.env['res.partner'].new({
            'name': 'Local Test Buyer',
            'country_id': self.env.ref('base.pe').id,
            'l10n_latam_identification_type_id': identity.id,
            'vat': number,
        })

    def test_missing_identity_is_not_fabricated(self):
        payer = self.env['res.partner'].new({'name': 'Local Test Buyer'})
        self.assertEqual(self.tx._mercado_pago_get_identification_values(payer), {})

    def test_peru_codes_map_independently_of_translated_names(self):
        for code, mp_type, number in [('1', 'DNI', '87654321'),
                                     ('4', 'CE', 'ABC123456'),
                                     ('6', 'RUC', '20601234567')]:
            with self.subTest(code=code):
                self.assertEqual(self.tx._mercado_pago_get_identification_values(
                    self._payer(code, number)), {'type': mp_type, 'number': number})

    def test_passport_and_missing_number_are_not_fabricated(self):
        self.assertEqual(self.tx._mercado_pago_get_identification_values(
            self._payer('7', 'LOCAL123')), {})
        self.assertEqual(self.tx._mercado_pago_get_identification_values(
            self._payer('1', False)), {})

    def test_payer_logging_redacts_personal_data_without_mutating_request(self):
        payload = {'items': [{'title': 'LOCAL TEST'}], 'payer': {
            'first_name': 'Test', 'last_name': 'Buyer', 'email': 'test@example.invalid',
            'phone': {'number': '+51900000000'},
            'address': {'street_name': 'Local test address'},
            'identification': {'type': 'DNI', 'number': '87654321'},
        }}
        redacted = self.tx._mercado_pago_redact_preference_payload_for_log(payload)
        self.assertEqual(redacted['payer'], '<REDACTED>')
        self.assertEqual(payload['payer']['identification']['number'], '87654321')
        self.assertEqual(redacted['items'], payload['items'])

    def test_optional_phone_does_not_access_removed_mobile_field(self):
        self.tx.partner_phone = False
        self.tx.partner_id.phone = False
        values = self.tx._mercado_pago_get_preference_payer_values()
        self.assertNotIn('phone', values)

    def test_diagnostic_parameter_cannot_replace_customer(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'payment_mercado_pago.debug_static_payer', 'True')
        values = self.tx._mercado_pago_get_preference_payer_values()
        self.assertNotEqual(values.get('email'), 'debug.mercadopago.static@example.com')

    def test_sandbox_rendering_uses_sandbox_url(self):
        with patch.object(type(self.tx), '_send_api_request', return_value={
            'init_point': 'https://live.example.invalid/?id=LOCAL',
            'sandbox_init_point': 'https://sandbox.example.invalid/?id=LOCAL',
        }) as send:
            values = self.tx._get_specific_rendering_values({})
        self.assertEqual(values['api_url'], 'https://sandbox.example.invalid/?id=LOCAL')
        self.assertEqual(send.call_args.args[:2], ('POST', '/checkout/preferences'))

    def test_provider_failure_becomes_payment_error(self):
        with patch.object(type(self.tx), '_send_api_request',
                          side_effect=ValidationError('LOCAL sandbox failure')):
            self.assertEqual(self.tx._get_specific_rendering_values({}), {})
        self.assertEqual(self.tx.state, 'error')

    def _verified_payment(self, amount=None, currency=None):
        return {'id': 'LOCAL-VERIFIED', 'status': 'approved',
                'external_reference': self.tx.reference,
                'currency_id': currency or self.tx.currency_id.name,
                'additional_info': {'items': [{'unit_price': amount}]}}

    def test_wrong_amount_is_rejected(self):
        self.tx._process('mercado_pago', self._verified_payment(self.tx.amount + 1))
        self.assertEqual(self.tx.state, 'error')

    def test_wrong_currency_is_rejected(self):
        self.tx._process('mercado_pago', self._verified_payment(self.tx.amount, 'PEN'))
        self.assertEqual(self.tx.state, 'error')

    def test_replayed_verified_payment_retains_state(self):
        data = self._verified_payment(self.tx.amount)
        self.tx._process('mercado_pago', data)
        self.tx._process('mercado_pago', data)
        self.assertEqual(self.tx.state, 'done')
        self.assertEqual(self.tx.provider_reference, 'LOCAL-VERIFIED')

    def test_missing_amount_is_rejected_without_exception(self):
        self.tx._process('mercado_pago', self._verified_payment())
        self.assertEqual(self.tx.state, 'error')

    def _verify_callback(self, reference):
        verified = self._verified_payment(self.tx.amount)
        verified.update(external_reference=reference, payer={'first_name':'PRIVATE TEST NAME','email':'private@example.invalid'})
        with patch.object(payment_controller, 'request', SimpleNamespace(env=self.env)), \
             patch.object(type(self.tx), '_send_api_request', return_value=verified), \
             patch.object(type(self.tx), '_process') as process, \
             patch.object(payment_controller._logger, 'info') as log:
            payment_controller.MercadoPagoPaymentController._verify_and_process(
                {'external_reference':self.tx.reference,'payment_id':'LOCAL-VERIFIED'})
        return process, log

    def test_mismatched_verified_reference_is_not_processed(self):
        process, _ = self._verify_callback('DIFFERENT LOCAL ORDER')
        process.assert_not_called()

    def test_missing_verified_reference_is_not_processed(self):
        process, _ = self._verify_callback(None)
        process.assert_not_called()

    def test_matching_callback_logs_no_payer_identity(self):
        process, log = self._verify_callback(self.tx.reference)
        process.assert_called_once()
        logged = str(log.call_args_list)
        self.assertNotIn('PRIVATE TEST NAME',logged)
        self.assertNotIn('example.invalid',logged)
