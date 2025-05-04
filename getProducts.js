function getProductElements() {
    const productElements = document.querySelectorAll('div.a-fixed-left-grid-col.yohtmlc-item.a-col-right, div.yohtmlc-product-title');
    const results = [];

    if (productElements.length > 0) {
        productElements.forEach((element, index) => {
            const rect = element.getBoundingClientRect();
            results.push({
                text: element.textContent.trim(),
                y: rect.top,
            });
        });
    } else {
        console.log("Keine passenden Elemente gefunden.");
    }

    return results;
}

return getProductElements();