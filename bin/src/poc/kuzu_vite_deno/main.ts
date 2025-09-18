// 最小限の実装でkuzu-wasmをテスト

// 型定義
type Result<T> = { data: T } | { error: string };

type AppState = {
  db: Database | null;
  conn: Connection | null;
};

type DOMElements = {
  initBtn: HTMLButtonElement;
  createBtn: HTMLButtonElement;
  queryBtn: HTMLButtonElement;
  statusDiv: HTMLDivElement;
  resultPre: HTMLPreElement;
};

type ResultData = {
  status?: string;
  message?: string;
  inMemory?: boolean;
  table?: string;
  records?: number;
  query?: string;
  rowCount?: number;
  data?: unknown[];
  error?: string;
};

// 状態管理
function createAppState(): AppState {
  return {
    db: null,
    conn: null
  };
}

// DOM要素取得
function getDOMElements(): Result<DOMElements> {
  const initBtn = document.getElementById('initBtn');
  const createBtn = document.getElementById('createBtn');
  const queryBtn = document.getElementById('queryBtn');
  const statusDiv = document.getElementById('status');
  const resultPre = document.getElementById('result');

  if (!initBtn || !createBtn || !queryBtn || !statusDiv || !resultPre) {
    return { error: 'Required DOM elements not found' };
  }

  return {
    data: {
      initBtn: initBtn as HTMLButtonElement,
      createBtn: createBtn as HTMLButtonElement,
      queryBtn: queryBtn as HTMLButtonElement,
      statusDiv: statusDiv as HTMLDivElement,
      resultPre: resultPre as HTMLPreElement
    }
  };
}

// ステータス表示関数
function showStatus(elements: DOMElements, message: string, isError: boolean) {
  elements.statusDiv.textContent = message;
  elements.statusDiv.className = isError ? 'error' : 'success';
  console.log(`[STATUS] ${message}`);
}

// 結果表示関数
function showResult(elements: DOMElements, data: ResultData) {
  elements.resultPre.textContent = JSON.stringify(data, null, 2);
}

async function testKuzu() {
  console.trace('[1] Import kuzu-wasm');
  const module = await import('kuzu-wasm');
  
  const kuzu = module.default;
  console.trace('[2] kuzu object keys:', Object.keys(kuzu));
  
  // init関数を実行
  console.trace('[3] Calling kuzu.init()');
  await kuzu.init();
  console.trace('[4] Init done');
  
  // Database と Connection を確認
  console.trace('[5] kuzu.Database:', kuzu.Database);
  console.trace('[6] kuzu.Connection:', kuzu.Connection);
  
  // インスタンス作成テスト
  try {
    console.trace('[7] Creating Database instance');
    const db = new kuzu.Database();
    console.trace('[8] Database created:', db);
    
    console.trace('[9] Creating Connection instance');
    const conn = new kuzu.Connection(db);
    console.trace('[10] Connection created:', conn);
    
    // バージョン確認
    console.trace('[11] Version:', kuzu.getVersion());
    console.trace('[12] Storage Version:', kuzu.getStorageVersion());
    
    return { db, conn };
  } catch (e) {
    console.trace('[ERROR]', e);
    throw e;
  }
}

// 初期化ボタンハンドラー
function setupInitButton(elements: DOMElements, state: AppState) {
  elements.initBtn.addEventListener('click', async () => {
    showStatus(elements, 'Testing...', false);
    await testKuzu();
    showStatus(elements, 'Check console', false);
  });
}

// テーブル作成関数
async function createPersonTable(conn: Connection): Promise<Result<{ table: string; records: number }>> {
  try {
    await conn.query(`
      CREATE NODE TABLE Person(
        name STRING,
        age INT64,
        PRIMARY KEY (name)
      )
    `);
    
    await conn.query(`CREATE (p:Person {name: 'Alice', age: 25})`);
    await conn.query(`CREATE (p:Person {name: 'Bob', age: 30})`);
    await conn.query(`CREATE (p:Person {name: 'Charlie', age: 35})`);
    
    return { data: { table: 'Person', records: 3 } };
  } catch (error) {
    return { error: String(error) };
  }
}

// テーブル作成ボタンハンドラー
function setupCreateButton(elements: DOMElements, state: AppState) {
  elements.createBtn.addEventListener('click', async () => {
    if (!state.conn) {
      showStatus(elements, '❌ データベース接続がありません', true);
      return;
    }
    
    showStatus(elements, '🔨 テーブル作成中...', false);
    
    const result = await createPersonTable(state.conn);
    
    if ('error' in result) {
      showStatus(elements, `❌ エラー: ${result.error}`, true);
      showResult(elements, { error: result.error });
      return;
    }
    
    showStatus(elements, '✅ テーブル作成完了！', false);
    elements.queryBtn.disabled = false;
    elements.createBtn.disabled = true;
    
    showResult(elements, {
      status: 'table_created',
      table: result.data.table,
      records: result.data.records
    });
  });
}

// クエリ実行関数
async function queryPersons(conn: Connection): Promise<Result<{ rows: unknown[]; query: string }>> {
  try {
    const query = `
      MATCH (p:Person)
      RETURN p.name AS name, p.age AS age
      ORDER BY p.age
    `;
    
    const result = await conn.query(query);
    const rows = [];
    
    while (result.hasNext()) {
      rows.push(result.getNext());
    }
    
    return { data: { rows, query: query.trim() } };
  } catch (error) {
    return { error: String(error) };
  }
}

// クエリ実行ボタンハンドラー
function setupQueryButton(elements: DOMElements, state: AppState) {
  elements.queryBtn.addEventListener('click', async () => {
    if (!state.conn) {
      showStatus(elements, '❌ データベース接続がありません', true);
      return;
    }
    
    showStatus(elements, '🔍 クエリ実行中...', false);
    
    const result = await queryPersons(state.conn);
    
    if ('error' in result) {
      showStatus(elements, `❌ エラー: ${result.error}`, true);
      showResult(elements, { error: result.error });
      return;
    }
    
    showStatus(elements, '✅ クエリ完了！', false);
    showResult(elements, {
      query: result.data.query,
      rowCount: result.data.rows.length,
      data: result.data.rows
    });
  });
}

// メインアプリケーション初期化
function initializeApp() {
  const elementsResult = getDOMElements();
  
  if ('error' in elementsResult) {
    console.error(elementsResult.error);
    return;
  }
  
  const elements = elementsResult.data;
  const state = createAppState();
  
  setupInitButton(elements, state);
  setupCreateButton(elements, state);
  setupQueryButton(elements, state);
  
  showStatus(elements, '🎯 KuzuDBを初期化してください', false);
}

// アプリケーション起動
initializeApp();