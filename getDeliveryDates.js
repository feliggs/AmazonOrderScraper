function getDeliveryTexts() {
    const deliveryTexts = document.querySelectorAll('span.a-size-medium.a-color-base.a-text-bold, span.a-size-medium.delivery-box__primary-text.a-text-bold');
    const results = [];

    if (deliveryTexts.length > 0) {
        deliveryTexts.forEach((text, index) => {
            const rect = text.getBoundingClientRect();
            results.push({
                text: text.textContent.trim(),
                y: rect.top
            });
        });
    } else {
        console.log("Keine passenden Lieferdatum-Elemente gefunden.");
    }

    return results;
}

return getDeliveryTexts();