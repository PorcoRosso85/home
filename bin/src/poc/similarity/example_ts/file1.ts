function calculateTotal(items: number[]): number {
    let total = 0;
    for (const item of items) {
        total += item;
    }
    return total;
}

function computeSum(numbers: number[]): number {
    let sum = 0;
    for (const num of numbers) {
        sum += num;
    }
    return sum;
}

function addNumbers(arr: number[]): number {
    let result = 0;
    arr.forEach(n => {
        result += n;
    });
    return result;
}