/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { WebsiteSale } from '@website_sale/interactions/website_sale';

patch(WebsiteSale.prototype, {
    _onChangeCombination(ev, parent, combination) {
        super._onChangeCombination(...arguments);

        const container = parent.querySelector('[name="product_price_container"]');
        const price = container?.querySelector('.o_vlizama_sale_price');
        const badge = container?.querySelector('.o_vlizama_discount_badge');
        if (!price || !badge) {
            return;
        }

        const reference = combination.has_discounted_price
            ? combination.list_price
            : combination.compare_list_price;
        // Match the precision of Odoo's displayed monetary amounts.
        const scale = 10 ** combination.currency_precision;
        const referenceUnits = Math.round(reference * scale);
        const saleUnits = Math.round(combination.price * scale);
        const hasDiscount = !combination.prevent_zero_price_sale &&
            Number.isFinite(reference) && Number.isFinite(combination.price) &&
            referenceUnits > saleUnits;
        const percent = hasDiscount
            ? Math.floor(100 * (referenceUnits - saleUnits) / referenceUnits)
            : 0;

        price.classList.toggle('o_vlizama_discounted', hasDiscount);
        badge.classList.toggle('d-none', percent < 1);
        badge.textContent = percent >= 1 ? `−${percent}%` : '';
        if (percent >= 1) {
            badge.setAttribute('aria-label', `${percent}% de descuento`);
        } else {
            badge.removeAttribute('aria-label');
        }
    },
});
