from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged
from odoo.addons.website_sale.controllers.main import WebsiteSale
from ..controllers import checkout


@tagged('post_install', '-at_install')
class TestPeruCheckoutValidation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.controller = checkout.WebsiteSalePeruCheckoutLock()
        self.request_patch = patch.object(checkout, 'request', SimpleNamespace(env=self.env))
        self.request_patch.start()
        self.addCleanup(self.request_patch.stop)

    def _validate(self, code, document):
        identity = self.env['l10n_latam.identification.type'].search([
            ('l10n_pe_vat_code', '=', code),
        ], limit=1)
        values = {'country_id': self.env.ref('base.pe').id,
                  'l10n_latam_identification_type_id': identity.id, 'vat': document}
        with patch.object(WebsiteSale, '_validate_address_values', return_value=(set(), set(), [])):
            return self.controller._validate_address_values(
                values, self.env['res.partner'], 'billing', True, '')

    def test_country_neutral_ce_is_available(self):
        codes = self.controller._get_allowed_pe_identification_types().mapped('l10n_pe_vat_code')
        self.assertIn('4', codes)
        self.assertTrue(set(codes) <= {'1', '4', '6', '7'})

    def test_inherited_address_template_compiles(self):
        self.env['ir.qweb']._compile('website_sale.address_form_fields')

    def test_invalid_dni_is_rejected(self):
        for document in ('ABC', '1234567', '123456789', '１２３４５６７８'):
            with self.subTest(document=document):
                invalid, _, messages = self._validate('1', document)
                self.assertIn('vat', invalid)
                self.assertTrue(messages)

    def test_valid_dni_retains_leading_zero(self):
        invalid, missing, _ = self._validate('1', '01234567')
        self.assertNotIn('vat', invalid | missing)

    def test_ruc_uses_existing_checksum_validator(self):
        self.assertIn('vat', self._validate('6', '20100047219')[0])
        self.assertNotIn('vat', self._validate('6', '20100047218')[0])

    def test_ce_nonempty_and_missing_document(self):
        self.assertNotIn('vat', self._validate('4', 'LOCAL-CE01')[0])
        self.assertIn('vat', self._validate('4', '')[1])

    def test_validation_message_is_spanish(self):
        with patch.object(checkout, 'request', SimpleNamespace(env=self.env(context=dict(self.env.context, lang='es_419')))):
            self.assertIn('El DNI debe contener exactamente 8 d\u00edgitos.', self._validate('1', 'ABC')[2])

    def test_foreign_country_and_identity_cannot_bypass_lock(self):
        values = {'country_id':self.env.ref('base.us').id,
                  'state_id':self.env.ref('base.state_us_1').id,
                  'l10n_latam_identification_type_id':self.env.ref('l10n_latam_base.it_vat').id}
        with patch.object(WebsiteSale, '_validate_address_values', return_value=(set(),set(),[])):
            invalid, _, _ = self.controller._validate_address_values(values,self.env['res.partner'],'billing',True,'')
        self.assertEqual(values['country_id'],self.env.ref('base.pe').id)
        self.assertFalse(values['state_id'])
        self.assertIn('l10n_latam_identification_type_id',invalid)
