{
    "name": "Website Sale Product Image Fit",
    "summary": "Responsive shop product image fitting for website_sale",
    "version": "19.0.1.0.0",
    "category": "Website/eCommerce",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": ["website_sale"],
    "data": [
        "views/website_sale_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_sale_product_image_fit/static/src/scss/website_sale_product_image_fit.scss",
        ],
    },
    "installable": True,
    "application": False,
}