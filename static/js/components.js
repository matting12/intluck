
document.addEventListener("DOMContentLoaded", () => {
    function loadTemplate(id) {
        const tpl = document.getElementById(id);
        if (!tpl) {
            console.error("Template not found:", id);
            return "";
        }
        return tpl.innerHTML;
    }

    customElements.define("navbar-component", class extends HTMLElement {
        connectedCallback() { this.innerHTML = loadTemplate("navbar-template"); }
    });

    customElements.define("search-form-component", class extends HTMLElement {
        connectedCallback() { this.innerHTML = loadTemplate("search-form-template"); }
    });

    customElements.define("footer-component", class extends HTMLElement {
        connectedCallback() { this.innerHTML = loadTemplate("footer-template"); }
    });
});
