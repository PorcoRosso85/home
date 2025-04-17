/**
 * uiComponents.ts
 * 
 * 共通UIコンポーネント
 */

/**
 * ヘッダーコンポーネントの作成
 * @param onRefresh 更新ボタンクリック時のコールバック
 * @returns HTMLElement
 */
export function createHeader(onRefresh: () => void): HTMLElement {
  const header = document.createElement('header');
  header.innerHTML = `
    <h1>関数型スキーマビューア</h1>
    <div class="controls">
      <button id="refresh-btn">更新</button>
    </div>
  `;
  
  // 更新ボタンのイベント設定
  const refreshBtn = header.querySelector('#refresh-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', onRefresh);
  }
  
  return header;
}

/**
 * メインコンテンツコンポーネントの作成
 * @returns HTMLElement
 */
export function createMainContent(): HTMLElement {
  const content = document.createElement('main');
  content.innerHTML = `
    <div class="split-view">
      <div id="directory-tree" class="panel"></div>
      <div id="dependency-view" class="panel"></div>
    </div>
  `;
  
  return content;
}

/**
 * コマンドパネルの作成
 * @returns HTMLElement
 */
export function createCommandPanel(): HTMLElement {
  const commandPanel = document.createElement('div');
  commandPanel.id = 'command-panel';
  commandPanel.className = 'panel command-panel';
  commandPanel.innerHTML = `
    <h2>コマンド</h2>
    <div id="command-list"></div>
  `;
  
  return commandPanel;
}

/**
 * フッターの作成
 * @returns HTMLElement
 */
export function createFooter(): HTMLElement {
  const footer = document.createElement('footer');
  footer.innerHTML = `
    <p>関数型スキーマ管理 &copy; 2025</p>
  `;
  
  return footer;
}

/**
 * ロード中表示の表示
 */
export function showLoading(): void {
  const loadingDiv = document.createElement('div');
  loadingDiv.id = 'loading-overlay';
  loadingDiv.innerHTML = '<div class="loading-spinner"></div>';
  document.body.appendChild(loadingDiv);
}

/**
 * ロード中表示の非表示
 */
export function hideLoading(): void {
  const loadingDiv = document.getElementById('loading-overlay');
  if (loadingDiv) {
    document.body.removeChild(loadingDiv);
  }
}

/**
 * エラー表示
 */
export function showError(message: string): void {
  const errorDiv = document.createElement('div');
  errorDiv.className = 'error-message';
  errorDiv.innerHTML = `
    <div class="error-content">
      <h3>エラー</h3>
      <p>${message}</p>
      <button id="close-error">閉じる</button>
    </div>
  `;
  
  document.body.appendChild(errorDiv);
  
  // 閉じるボタンのイベント設定
  const closeBtn = document.getElementById('close-error');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      document.body.removeChild(errorDiv);
    });
  }
}
