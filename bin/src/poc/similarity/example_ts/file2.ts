function sumArray(values: number[]): number {
    let total = 0;
    for (const val of values) {
        total += val;
    }
    return total;
}

function getTotalAmount(prices: number[]): number {
    let amount = 0;
    prices.forEach(price => {
        amount += price;
    });
    return amount;
}