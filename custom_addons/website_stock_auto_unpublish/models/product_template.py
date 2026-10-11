import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _cron_unpublish_out_of_stock_website_products(self, limit=500):
        """
        Unpublish website products when their on-hand stock is zero or negative.

        Notes:
        - Uses ORM, not raw SQL.
        - Does not republish products automatically.
        - Ignores services and combo products.
        """

        domain = [
            ("is_published", "=", True),
            ("sale_ok", "=", True),
            ("type", "not in", ["service", "combo"]),
            ("qty_available", "<=", 0),
        ]

        products = self.search(domain, limit=limit)

        if products:
            products.write({"is_published": False})
            _logger.info(
                "Website Stock Auto Unpublish: unpublished %s out-of-stock products: %s",
                len(products),
                ", ".join(products.mapped("display_name")),
            )

        remaining = self.search_count(domain)
        self.env["ir.cron"]._commit_progress(len(products), remaining=remaining)

        return True