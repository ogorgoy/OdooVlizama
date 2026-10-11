from odoo import _
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSalePeruCheckoutLock(WebsiteSale):
    """Restrict website checkout address data for Peru."""

    # Allowed Peru identification types:
    # 1 = DNI
    # 4 = Carnet de Extranjería
    # 6 = RUC
    # 7 = Passport
    _ALLOWED_PE_VAT_CODES = ("1", "4", "6", "7")

    def _get_peru_country(self):
        """Return Peru country record."""
        return (
            request.env.ref("base.pe", raise_if_not_found=False)
            or request.env["res.country"].sudo().search([("code", "=", "PE")], limit=1)
        )

    def _get_allowed_pe_identification_types(self):
        """Return the allowed Peruvian identification types for checkout."""
        identification_type_model = request.env["l10n_latam.identification.type"].sudo()
        peru = self._get_peru_country()
        if not peru:
            return identification_type_model.browse()

        domain = [("country_id", "=", peru.id)]

        if "l10n_pe_vat_code" in identification_type_model._fields:
            domain.append(("l10n_pe_vat_code", "in", list(self._ALLOWED_PE_VAT_CODES)))

        identification_types = identification_type_model.search(domain, order="sequence, name, id")

        # Fallback in case the field is not present or values differ in the database
        if not identification_types:
            identification_types = identification_type_model.search(
                [("country_id", "=", peru.id)],
                order="sequence, name, id",
            )

        return identification_types

    def _prepare_address_form_values(self, *args, callback="", order_sudo=False, **kwargs):
        """Force the checkout form to use Peru-only country data."""
        values = super()._prepare_address_form_values(
            *args,
            callback=callback,
            order_sudo=order_sudo,
            **kwargs,
        )

        peru = self._get_peru_country()
        if not peru:
            values["pe_checkout_identification_types"] = (
                request.env["l10n_latam.identification.type"].sudo().browse()
            )
            return values

        address_fields = peru.get_address_fields() or ["city", "zip"]
        zip_before_city = (
            "zip" in address_fields
            and "city" in address_fields
            and address_fields.index("zip") < address_fields.index("city")
        )

        values.update(
            {
                "country": peru,
                "countries": peru,
                "country_states": peru.state_ids,
                "zip_before_city": zip_before_city,
                "can_edit_country": True,
                "pe_checkout_identification_types": self._get_allowed_pe_identification_types(),
            }
        )

        state_id = values.get("state_id")
        if state_id and state_id not in peru.state_ids.ids:
            values["state_id"] = False

        return values

    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        **kwargs,
    ):
        """Enforce Peru country and restrict allowed identification types."""
        peru = self._get_peru_country()
        allowed_identification_types = self._get_allowed_pe_identification_types()
        allowed_identification_type_ids = set(allowed_identification_types.ids)

        if peru:
            address_values["country_id"] = peru.id

            state_id = address_values.get("state_id")
            if state_id and state_id not in peru.state_ids.ids:
                address_values["state_id"] = False

        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            required_fields,
            **kwargs,
        )

        selected_identification_type_id = address_values.get("l10n_latam_identification_type_id")
        if (
            selected_identification_type_id
            and allowed_identification_type_ids
            and selected_identification_type_id not in allowed_identification_type_ids
        ):
            invalid_fields.add("l10n_latam_identification_type_id")
            error_messages.append(
                _("The selected identification type is not allowed for Peru checkout.")
            )

        return invalid_fields, missing_fields, error_messages