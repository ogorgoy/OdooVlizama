{
    "name": "Website WhatsApp Floating Button",
    "summary": "Floating WhatsApp button with context-aware messages",
    "version": "19.0.1.0.0",
    "category": "Website",
    "license": "LGPL-3",
    "author": "Custom",
    "depends": ["website", "website_sale"],
    "data": [
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "website_whatsapp_float/static/src/scss/whatsapp_float.scss",
            "website_whatsapp_float/static/src/js/whatsapp_float.js",
        ],
    },
    "installable": True,
    "application": False,
}

