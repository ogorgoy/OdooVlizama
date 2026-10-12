# Odoo 19 Mercado Pago safety patch

This patch targets the customized Odoo 19 provider used in the development validation. It is not an automatically installed addon and must be reviewed against the deployed provider source before application.

`payment-safety.patch` is relative to the provider addon directory. The `tests/` files accompany the patch and replace the matching provider test files; other native tests remain in place.

Changes:

- Remove fabricated DNI and static diagnostic payer substitution.
- Map genuine Peru identification codes; omit missing/unsupported identification.
- Remove obsolete partner mobile-field access and redact payer logs.
- Reject missing/invalid payment amounts through the existing validator.
- Ignore callback payments whose verified reference is missing or belongs to another transaction; log metadata only.

Validation performed on 11 October 2026: 25 native provider tests and eight custom checkout tests passed, using mocked provider responses. Four stock checks and two cancellation/stock-release checks passed with database changes rolled back. These results do not establish external Mercado Pago compatibility or production parity.

Before production rollout, test on a matched isolated Odoo 19 environment with verified sandbox credentials and HTTPS callbacks. Verify approved/pending/rejected/refund outcomes and concurrent duplicate callbacks. Core provider edits can be overwritten by Odoo upgrades; retain and revalidate the patch. No credentials, databases, customer records or production configuration are included here.
