// 完全に同じ関数
function processData(data: any[]) {
    const result = [];
    for (const item of data) {
        if (item.active) {
            result.push(item);
        }
    }
    return result;
}

// 変数名だけ違う
function filterActiveItems(items: any[]) {
    const filtered = [];
    for (const element of items) {
        if (element.active) {
            filtered.push(element);
        }
    }
    return filtered;
}

// 少し構造が違う
function getActiveRecords(records: any[]) {
    return records.filter(record => record.active);
}