function getProductElements() {
    const productElements = document.querySelectorAll('.item-view-left-col-inner, .product-image');
    const results = [];

    if (productElements.length > 0) {
        productElements.forEach((element) => {
            const rect = element.getBoundingClientRect();
            results.push({
                html: element.outerHTML,
                y: rect.top,
            });
        });
    } else {
        return "Keine passenden Elemente gefunden.";
    }

    return results;
}

return getProductElements();