import re
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

        # CE/passport are country-neutral localization records, unlike DNI/RUC.
        domain = [
            ("l10n_pe_vat_code", "in", self._ALLOWED_PE_VAT_CODES),
            "|", ("country_id", "=", peru.id), ("country_id", "=", False),
        ]
        return identification_type_model.search(domain, order="sequence, name, id")

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
            and selected_identification_type_id not in allowed_identification_type_ids
        ):
            invalid_fields.add("l10n_latam_identification_type_id")
            error_messages.append(
                request.env._("The selected identification type is not allowed for Peru checkout.")
            )

        if selected_identification_type_id in allowed_identification_type_ids and (
            address_type == "billing" or use_delivery_as_billing
        ):
            identity = allowed_identification_types.browse(selected_identification_type_id)
            document = (address_values.get("vat", partner_sudo.vat or "") or "").strip()
            if not document:
                missing_fields.add("vat")
                error_messages.append(request.env._("Enter your identification number."))
            elif identity.l10n_pe_vat_code == "1" and not re.fullmatch(r"[0-9]{8}", document):
                invalid_fields.add("vat")
                error_messages.append(request.env._("DNI must contain exactly 8 digits."))
            elif identity.l10n_pe_vat_code == "6" and (
                not re.fullmatch(r"[0-9]{11}", document)
                or not request.env["res.partner"].check_vat_pe(document)
            ):
                if "vat" not in invalid_fields:
                    error_messages.append(request.env._("Enter a valid 11-digit RUC."))
                invalid_fields.add("vat")

        return invalid_fields, missing_fields, error_messages
