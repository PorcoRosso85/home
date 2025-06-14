/**
 * 依存関係グラフの可視化を行うクラス
 * コールスタックを意識したDAG表現を構築する
 */
export class DependencyGraphVisualizer {
  // 依存関係マップ (関数名 -> 依存関数名の配列)
  private dependencyMap: Map<string, string[]>;
  
  // 実行順序を格納 (関数名 -> 実行順序の配列)
  private executionOrderMap: Map<string, Map<string, number>>;
  
  // 可視化のためのグリッド
  private grid: string[][];
  
  // グリッドの幅と高さ
  private width: number;
  private height: number;
  
  /**
   * コンストラクタ
   * 
   * @param dependencyMap 依存関係マップ (関数名 -> 依存関数名の配列)
   * @param executionOrderMap 実行順序マップ (関数名 -> (依存関数名 -> 実行順序))
   */
  constructor(
    dependencyMap: Map<string, string[]>,
    executionOrderMap?: Map<string, Map<string, number>>
  ) {
    this.dependencyMap = dependencyMap;
    this.executionOrderMap = executionOrderMap || new Map();
    this.width = 0;
    this.height = 0;
    this.grid = [];
  }
  
  /**
   * 依存関係グラフをDAG形式で可視化する
   * 
   * @param maxWidth 最大幅
   * @returns 可視化されたグラフの行配列
   */
  public visualize(maxWidth: number = 100): string[][] {
    // 全関数のリスト
    const allFunctions = this.getAllFunctions();
    
    // 表示対象の関数が無ければ空の配列を返す
    if (allFunctions.length === 0) {
      return [];
    }
    
    // グラフの初期化 - 幅を充分に取る
    this.initializeGraph(allFunctions, maxWidth);
    
    // グラフの構築
    this.buildGraph(allFunctions);
    
    // 最終的なグラフの構築（関数名とパスを追加するための空の列）
    const result: string[][] = new Array(this.height);
    for (let y = 0; y < this.height; y++) {
      result[y] = ['', ...this.grid[y]];
    }
    
    return result;
  }
  
  /**
   * すべての関数を取得（重複なし）
   */
  private getAllFunctions(): string[] {
    const functionSet = new Set<string>();
    
    // 親関数を追加
    for (const func of this.dependencyMap.keys()) {
      functionSet.add(func);
    }
    
    // 依存関数を追加
    for (const deps of this.dependencyMap.values()) {
      for (const dep of deps) {
        functionSet.add(dep);
      }
    }
    
    // 配列に変換してソート
    return [...functionSet].sort();
  }
  
  /**
   * グラフの初期化
   * 
   * @param functions 全関数のリスト
   * @param maxWidth 最大幅
   */
  private initializeGraph(functions: string[], maxWidth: number): void {
    this.height = functions.length;
    
    // 最大依存深度を計算して幅を決定
    const maxDepth = this.getMaxDependencyDepth();
    // 各依存に対して表現用の幅を確保
    this.width = Math.min(maxWidth, maxDepth * 6 + 1);
    
    // グリッドを空白で初期化
    this.grid = new Array(this.height);
    for (let y = 0; y < this.height; y++) {
      this.grid[y] = new Array(this.width).fill(' ');
    }
  }
  
  /**
   * 最大依存深度を計算
   */
  private getMaxDependencyDepth(): number {
    let maxDepth = 0;
    
    // 各関数について依存の深さを計算
    for (const func of this.dependencyMap.keys()) {
      const deps = this.dependencyMap.get(func) || [];
      if (deps.length > maxDepth) {
        maxDepth = deps.length;
      }
    }
    
    // next.mdの例に合わせて、より広い可視化領域を確保
    return Math.max(maxDepth, 5);
  }
  
  /**
   * グラフの構築
   * 
   * @param functions 全関数のリスト
   */
  private buildGraph(functions: string[]): void {
    // 関数の位置マップを構築
    const functionPositionMap = new Map<string, number>();
    for (let i = 0; i < functions.length; i++) {
      functionPositionMap.set(functions[i], i);
    }
    
    // 各関数の依存関係を描画
    for (const func of functions) {
      const deps = this.dependencyMap.get(func) || [];
      if (deps.length === 0) continue;
      
      const funcPos = functionPositionMap.get(func)!;
      this.drawDependencies(func, deps, funcPos, functionPositionMap);
    }
  }
  
  /**
   * 依存関係を描画
   * 
   * @param func 親関数
   * @param deps 依存関数配列
   * @param funcPos 親関数の位置
   * @param functionPositionMap 関数位置マップ
   */
  private drawDependencies(
    func: string, 
    deps: string[], 
    funcPos: number,
    functionPositionMap: Map<string, number>
  ): void {
    // 実行順序でソート
    const sortedDeps = [...deps].sort((a, b) => {
      const orderA = this.getExecutionOrder(func, a);
      const orderB = this.getExecutionOrder(func, b);
      return orderA - orderB;
    });
    
    // 各依存関係を描画
    let xOffset = 2; // 初期のX位置オフセット
    
    // 最初の矢印を描画
    for (let i = 0; i < 2; i++) {
      if (i < this.width) this.grid[funcPos][i] = '→';
    }
    
    for (const dep of sortedDeps) {
      const depPos = functionPositionMap.get(dep);
      if (depPos === undefined) continue;
      
      // 依存関係の描画、next.mdの例に合わせて距離を広げて可視性を向上
      this.drawSingleDependency(func, dep, funcPos, depPos, xOffset);
      
      // 次の描画位置にオフセット - より広い間隔で表示
      xOffset += 10;
    }
  }
  
  /**
   * 単一の依存関係を描画
   * 
   * @param func 親関数
   * @param dep 依存関数
   * @param funcPos 親関数の位置
   * @param depPos 依存関数の位置
   * @param xOffset X位置オフセット
   */
  private drawSingleDependency(
    func: string,
    dep: string,
    funcPos: number,
    depPos: number,
    xOffset: number
  ): void {
    // next.mdの例に合わせた表示構造に変更

    // 親関数から依存関数への矢印を複数描画（ネクスト例に合わせて）
    for (let i = 0; i < 3; i++) {
      if (xOffset + i < this.width) this.grid[funcPos][xOffset + i] = '→';
    }

    // 依存関係の方向によって適切な接続パターンを描画
    if (funcPos < depPos) {
      // 下方向への接続 (親が上にある場合)
      // 現在の行のコネクタ追加
      if (xOffset + 2 < this.width) this.grid[funcPos][xOffset + 2] = '└';
      if (xOffset + 3 < this.width) this.grid[funcPos][xOffset + 3] = '┘';
      
      // 次行から最終行までの接続リンク
      for (let y = funcPos + 1; y < depPos; y++) {
        if (xOffset + 2 < this.width) this.grid[y][xOffset + 2] = '|';
        if (xOffset + 3 < this.width) this.grid[y][xOffset + 3] = '|';
      }
      
      // 最終行のコネクタ
      if (xOffset + 2 < this.width) this.grid[depPos][xOffset + 2] = '└';
      if (xOffset + 3 < this.width) this.grid[depPos][xOffset + 3] = '┘';
      
    } else if (funcPos > depPos) {
      // 上方向への接続 (親が下にある場合)
      // 現在の行のコネクタ追加
      if (xOffset + 2 < this.width) this.grid[funcPos][xOffset + 2] = '┌';
      if (xOffset + 3 < this.width) this.grid[funcPos][xOffset + 3] = '┐';
      
      // 最終行から次行までの接続リンク
      for (let y = depPos; y < funcPos; y++) {
        if (xOffset + 2 < this.width) this.grid[y][xOffset + 2] = '|';
        if (xOffset + 3 < this.width) this.grid[y][xOffset + 3] = '|';
      }
      
      // 最初の行のコネクタ
      if (xOffset + 2 < this.width) this.grid[depPos][xOffset + 2] = '┌';
      if (xOffset + 3 < this.width) this.grid[depPos][xOffset + 3] = '┐';
    }
  }
  
  /**
   * 実行順序を取得
   * 
   * @param func 親関数
   * @param dep 依存関数
   * @returns 実行順序（デフォルトは依存関数のインデックス）
   */
  private getExecutionOrder(func: string, dep: string): number {
    // 実行順序マップがあればそれを使用
    const orderMap = this.executionOrderMap.get(func);
    if (orderMap && orderMap.has(dep)) {
      return orderMap.get(dep)!;
    }
    
    // なければ依存配列中のインデックスを使用
    const deps = this.dependencyMap.get(func) || [];
    const index = deps.indexOf(dep);
    return index >= 0 ? index : 999; // 見つからない場合は大きな値
  }
}
