# Odoo 19 Website & eCommerce Addons

Custom addons for an Odoo 19 Community storefront, covering mobile navigation, catalog presentation, product images, Peruvian checkout identification, stock-based publication, and WhatsApp contact links.

This repository contains the custom modules only. Odoo, its Python runtime, PostgreSQL, database contents, and filestore are managed separately.

## Modules

| Module | Purpose | Direct dependencies |
| --- | --- | --- |
| `website_mobile_drawer_menu` | Mobile drawer navigation with icons and mobile header styling, including scroll-state positioning. | `website`, `website_sale` |
| `website_sale_product_image_fit` | Responsive catalog image fitting, desktop secondary-image presentation, and mobile image slides. | `website_sale` |
| `website_sale_catalog_layout` | Compact catalog list cards, search controls, discount price styling, and percentage badges on catalog and product pages. Updates product badges when variants change. | `website_sale_product_image_fit` |
| `website_sale_identification_type` | Forces checkout country to Peru and validates DNI/RUC/CE identification. | `website_sale`, `l10n_latam_base`, `l10n_pe` |
| `website_stock_auto_unpublish` | Scheduled removal of published products with zero or negative on-hand stock. | `website_sale`, `stock` |
| `website_whatsapp_float` | Floating WhatsApp links on the homepage, shop, and product pages, with context-aware Spanish messages. | `website`, `website_sale` |

Install only the modules needed for your storefront. Odoo resolves declared dependencies; installing the catalog layout also installs the product image module.

## Requirements

- A working Odoo 19 Community installation with its supported Python and PostgreSQL environment.
- Access to the active Odoo configuration and the ability to restart its process or service.
- The Odoo addons listed in the dependency table. The checkout module requires the Peruvian localization addons.

The modules target Odoo 19 templates and APIs. Compatibility with other Odoo versions has not been established.

## Repository structure

```text
custom_addons/
├── website_mobile_drawer_menu/       # QWeb templates, styles, and icons
├── website_sale_catalog_layout/      # QWeb, SCSS, and discount JavaScript
├── website_sale_identification_type/ # Checkout controller and QWeb fields
├── website_sale_product_image_fit/   # QWeb and image SCSS
├── website_stock_auto_unpublish/     # Product model extension and cron record
├── website_whatsapp_float/           # QWeb, SCSS, and WhatsApp JavaScript
└── README.md
```

Each module declares its dependencies, data files, frontend assets where applicable, and license in `__manifest__.py`.

## Installation

1. Clone or copy this repository into your custom addons directory. Keep each module directory directly inside that directory.
2. Add the repository directory to `addons_path` in the configuration actually used by Odoo. Retain all existing required addon paths.

   Example for the local Windows layout:

   ```ini
   [options]
   addons_path = D:\Odoo19Dev\custom_addons,D:\Odoo19Dev\server\odoo\addons
   ```

3. Restart Odoo.
4. Enable developer mode, open **Apps**, and run **Update Apps List**. Remove the default **Apps** filter if the modules are not visible: these modules declare `application = False`.
5. Find the module by its display name from its manifest and install it in the intended database.

Alternatively, install a module from PowerShell using the local runtime:

```powershell
& 'D:\Odoo19Dev\python\python.exe' 'D:\Odoo19Dev\server\odoo-bin' `
  -c 'D:\Odoo19Dev\dev.conf' -d '<database>' `
  -i website_sale_catalog_layout --stop-after-init --no-http
```

Replace `<database>` and filesystem paths with your deployment values. Run initialization or upgrade commands with the normal Odoo process stopped for that database, then restart it afterward.

## Local development and updates

For the existing Windows development layout, start Odoo with:

```powershell
& 'D:\Odoo19Dev\python\python.exe' 'D:\Odoo19Dev\server\odoo-bin' `
  -c 'D:\Odoo19Dev\dev.conf'
```

The current local configuration uses port `8079`; open `http://localhost:8079` while Odoo is running. Other installations should use their configured port.

After changing a module, upgrade it in the intended database:

```powershell
& 'D:\Odoo19Dev\python\python.exe' 'D:\Odoo19Dev\server\odoo-bin' `
  -c 'D:\Odoo19Dev\dev.conf' -d '<database>' `
  -u website_mobile_drawer_menu --stop-after-init --no-http
```

Use the relevant module name, or a comma-separated list for related changes. Restart Odoo afterward and refresh the browser. For frontend troubleshooting, use Odoo's `?debug=assets` mode and inspect the browser console and Odoo logs. SCSS and JavaScript are loaded through Odoo assets; this repository has no separate frontend build step.

## Store-specific behavior and customization

### Mobile navigation and catalog

- Drawer templates and styles live in `website_mobile_drawer_menu/views/website_templates.xml`; icon assets live under `static/src/img/`.
- Catalog structure and prices live in `website_sale_catalog_layout/views/`. Card styling lives in `static/src/scss/catalog_layout.scss`; variant badge updates live in `static/src/js/discount_prices.js`.
- Product image behavior lives in `website_sale_product_image_fit/views/website_sale_views.xml` and `static/src/scss/website_sale_product_image_fit.scss`.
- Discount badges use Odoo-provided price values. Configure products and pricelists in Odoo; this addon changes their presentation.

### Peruvian checkout

The checkout controller forces Peru as the country and clears states outside Peru. Its preferred identification codes are DNI (`1`), Carnet de Extranjeria (`4`), RUC (`6`), and Passport (`7`). If the filtered lookup returns no records, the implementation falls back to the available Peruvian identification types. Confirm the localization records in your database before relying on a strict four-type restriction.

The behavior is implemented in `website_sale_identification_type/controllers/checkout.py` and `views/website_sale_templates.xml`.

### Stock-based unpublishing

The module creates an active scheduled action named **Unpublish Out of Stock Website Products**, initially running every 15 minutes as the system user.

- Selects published, saleable product templates with `qty_available <= 0`.
- Excludes service and combo products.
- Processes up to 500 products per method invocation and reports remaining work to Odoo's scheduler.
- Does **not** automatically republish products after restocking.

This uses on-hand stock, rather than forecast or website-specific availability. Review the behavior against your inventory and company setup before enabling it. Manage the action in developer mode under **Settings > Technical > Automation > Scheduled Actions**. Its XML record uses `noupdate="1"`, so later module upgrades normally preserve existing scheduled-action settings.

### WhatsApp contact

Edit `website_whatsapp_float/views/templates.xml` to set the destination number and messages. Update `data-wa-phone` in all three page templates, using the international country code and number without a leading `+`.

The module currently contains a store-specific number and Spanish messages. Message placeholders include `{category}`, `{product}`, and `{url}`. Product messages include the current page URL. There is no backend settings screen for these values.

## Verification

No automated test suite is included in this repository. Validate changes in a development or staging database with the modules installed:

- Open the homepage, shop, category, and product pages on desktop and mobile.
- Check the mobile drawer and header at page top, early scroll, and deep scroll.
- Check catalog grid/list presentation, single and secondary product images, and mobile image swiping.
