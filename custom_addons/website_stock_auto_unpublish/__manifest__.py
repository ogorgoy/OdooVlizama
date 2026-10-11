{
    "name": "Website Stock Auto Unpublish",
    "version": "19.0.1.0.0",
    "category": "Website/eCommerce",
    "summary": "Automatically unpublish website products when stock reaches zero.",
    "author": "Custom",
    "license": "LGPL-3",
    "depends": [
        "website_sale",
        "stock",
    ],
    "data": [
        "data/ir_cron.xml",
    ],
    "installable": True,
    "application": False,
}