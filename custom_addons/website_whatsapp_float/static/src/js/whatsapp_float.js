/** @odoo-module **/

function _safeTrim(s) {
    return (s || "").toString().trim();
}

function _encodeText(text) {
    return encodeURIComponent(text);
}

function _formatPhone(rawPhone) {
    const digits = (rawPhone || "").toString().replace(/\D/g, "");
    return digits;
}

function _getCategoryName() {
    const header = document.querySelector("#o_wsale_products_header");
    const name = header && header.dataset ? header.dataset.categoryName : "";
    return _safeTrim(name);
}

function _getProductName() {
    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle && _safeTrim(ogTitle.content)) {
        return _safeTrim(ogTitle.content);
    }

    const h1 =
        document.querySelector("#product_details h1") ||
        document.querySelector("#product_detail h1") ||
        document.querySelector("h1");
    if (h1 && _safeTrim(h1.textContent)) {
        return _safeTrim(h1.textContent);
    }
    return _safeTrim(document.title);
}

function _applyTemplate(tpl, replacements) {
    let out = tpl || "";
    for (const [key, value] of Object.entries(replacements || {})) {
        out = out.replaceAll(`{${key}}`, value);
    }
    return out;
}

function _buildMessage(el) {
    const page = _safeTrim(el.dataset.waPage);
    const defaultMsg = _safeTrim(el.dataset.waMsgDefault);
    const categoryTpl = _safeTrim(el.dataset.waMsgCategory);
    const productTpl = _safeTrim(el.dataset.waMsgProduct);

    if (page === "shop") {
        const category = _getCategoryName();
        if (category) {
            return _applyTemplate(categoryTpl || defaultMsg, { category });
        }
        return defaultMsg;
    }

    if (page === "product") {
        const product = _getProductName();
        const url = window.location.href;
        return _applyTemplate(productTpl || defaultMsg, { product, url });
    }

    // home (or fallback)
    return defaultMsg;
}

function _updateWhatsAppLink(el) {
    const phone = _formatPhone(el.dataset.waPhone);
    if (!phone) {
        return;
    }
    const text = _buildMessage(el);
    const href = `https://wa.me/${phone}?text=${_encodeText(text)}`;
    el.setAttribute("href", href);
}

function _updateLiftState(el) {
    const hasFloatingBar = Boolean(document.querySelector("#o_wsale_floating_bar"));
    el.classList.toggle("o_whatsapp_float--lifted", hasFloatingBar);
}

function _boot() {
    const buttons = document.querySelectorAll("a.o_whatsapp_float");
    if (!buttons.length) return;

    for (const btn of buttons) {
        _updateWhatsAppLink(btn);
        _updateLiftState(btn);
    }

    // Keep updated if shop filters are changed via client-side navigation.
    const header = document.querySelector("#o_wsale_products_header");
    if (header) {
        const observer = new MutationObserver(() => {
            for (const btn of buttons) {
                _updateWhatsAppLink(btn);
                _updateLiftState(btn);
            }
        });
        observer.observe(header, { attributes: true, attributeFilter: ["data-category-name"] });
    }

    window.addEventListener("resize", () => {
        for (const btn of buttons) {
            _updateLiftState(btn);
        }
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", _boot);
} else {
    _boot();
}

