{
    "name": "Website Sale Catalog Layout",
    "summary": "Compact list cards and standard catalog search controls",
    "version": "19.0.1.0.0",
    "category": "Website/eCommerce",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["website_sale_product_image_fit"],
    "data": ["views/website_sale_views.xml", "views/discount_prices.xml"],
    "assets": {
        "web.assets_frontend": [
            "website_sale_catalog_layout/static/src/scss/catalog_layout.scss",
            "website_sale_catalog_layout/static/src/js/discount_prices.js",
        ],
    },
    "installable": True,
    "application": False,
}
