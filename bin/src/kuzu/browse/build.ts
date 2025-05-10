import { createServer } from "npm:vite";
import wasmPlugin from "npm:vite-plugin-wasm";
import topLevelAwait from "npm:vite-plugin-top-level-await";
import path from "node:path";
import { parse } from "https://deno.land/std@0.180.0/flags/mod.ts";

/**
 * マウント定義の型
 */
interface MountDefinition {
  sourcePath: string;  // マウント元パス（実ファイルシステム上）
  targetPath: string;  // マウント先パス（URL上）
  filePattern?: string; // ファイルパターン（例: *.cypher）
}

/**
 * マウント文字列をパースする
 * 
 * 形式: "ソースパス:ターゲットパス[:ファイルパターン]"
 * 例: "/home/user/queries:/queries:*.cypher"
 * 
 * @param mountString マウント文字列
 * @returns マウント定義オブジェクト
 */
function parseMountString(mountString: string): MountDefinition {
  const parts = mountString.split(':');
  if (parts.length < 2) {
    throw new Error(`無効なマウント文字列です: ${mountString}。'ソースパス:ターゲットパス[:ファイルパターン]'の形式で指定してください。`);
  }

  const sourcePath = parts[0];
  const targetPath = parts[1].startsWith('/') ? parts[1] : `/${parts[1]}`;
  const filePattern = parts[2] || '*';

  return { sourcePath, targetPath, filePattern };
}

/**
 * コマンドライン引数を解析する
 * 
 * @returns 引数の解析結果
 */
function parseCommandLineArgs() {
  // 引数の解析
  const args = parse(Deno.args, {
    string: ["mount"],
    boolean: ["help"],
    alias: {
      "m": "mount",
      "h": "help",
    },
    collect: ["mount"], // 複数の--mountオプションを配列として収集
  });

  // ヘルプの表示
  if (args.help) {
    console.log(`
KuzuDB ブラウザ - 開発サーバー

使用方法:
  deno run -A build.ts --mount SOURCE_PATH:TARGET_PATH[:FILE_PATTERN] [--mount ...]

オプション:
  --mount SOURCE_PATH:TARGET_PATH[:PATTERN], -m   マウント設定（複数指定可能）
    SOURCE_PATH: マウント元のファイルシステムパス（例: /home/nixos/bin/src/kuzu/query/ddl）
    TARGET_PATH: マウント先のURLパス（例: /ddl）
    FILE_PATTERN: オプションのファイルパターン（例: *.cypher、デフォルト: *）

  例:
    --mount /home/nixos/bin/src/kuzu/query/ddl:/ddl:*.cypher
    --mount /home/nixos/bin/src/kuzu/query/dml:/dml
    --mount /path/to/public:/

  複数のマウント指定:
    --mount /path1:/api --mount /path2:/data

  --help, -h              このヘルプメッセージを表示
`);
    Deno.exit(0);
  }

  // mount オプションのデフォルト値を設定（空の配列）
  if (!args.mount || (Array.isArray(args.mount) && args.mount.length === 0)) {
    args.mount = [];
  } else if (!Array.isArray(args.mount)) {
    // 単一の値を配列に変換
    args.mount = [args.mount];
  }

  // マウント設定のパース
  const mounts: MountDefinition[] = [];
  try {
    for (const mountStr of args.mount) {
      mounts.push(parseMountString(mountStr));
    }
  } catch (error) {
    console.error(`マウント設定のパースエラー: ${error.message}`);
    Deno.exit(1);
  }

  // マウント元パスの存在チェック
  const invalidMounts: MountDefinition[] = [];
  for (const mount of mounts) {
    try {
      const stat = Deno.statSync(mount.sourcePath);
      if (!stat.isDirectory) {
        invalidMounts.push(mount);
        console.error(`エラー: マウント元パス "${mount.sourcePath}" はディレクトリではありません。`);
      }
    } catch (e) {
      invalidMounts.push(mount);
      console.error(`エラー: マウント元パス "${mount.sourcePath}" が存在しないか、アクセスできません。`);
    }
  }

  // 無効なマウントがある場合はエラー終了
  if (invalidMounts.length > 0) {
    console.error(`\n${invalidMounts.length} 個の無効なマウント設定がありました。`);
    console.error('詳細については --help オプションを指定して実行してください。');
    Deno.exit(1);
  }

  return { mounts };
}

// 開発サーバーの起動
async function createViteDevServer(mounts: MountDefinition[]) {
  // 許可するファイルシステムパスのリスト
  const allowPaths = ['.', '..', '/'];
  
  // マウント設定をfsAllowパスリストに追加
  for (const mount of mounts) {
    allowPaths.push(mount.sourcePath);
  }

  // Vite設定
  const config = {
    configFile: false,
    root: ".",
    publicDir: "public", // デフォルトのpublicディレクトリを使用
    plugins: [
      // NOTE: プラグインの順番が重要 - wasmプラグインを先に適用し、次にtopLevelAwaitプラグインを適用
      wasmPlugin(),  // WASMモジュールをESM形式で使用可能にする
      topLevelAwait(), // トップレベルでのawait使用を可能にする
      // カスタムプラグイン: ブラウザログをサーバーに転送
      {
        name: 'vite-console-redirect-plugin',
        transformIndexHtml: {
          enforce: 'pre',
          transform(html) {
            // インデックスHTMLに挿入するスクリプト
            const script = `
              <script>
                // 元のコンソールメソッドを保存
                const originalConsole = {
                  log: console.log,
                  error: console.error,
                  warn: console.warn,
                  info: console.info
                };
                
                // コンソール関数をオーバーライド
                function overrideConsole(method) {
                  console[method] = function(...args) {
                    // 元の機能を呼び出し
                    originalConsole[method].apply(console, args);
                    
                    // サーバーに送信
                    try {
                      const message = args.map(arg => {
                        if (typeof arg === 'object') {
                          return JSON.stringify(arg, null, 2);
                        }
                        return String(arg);
                      }).join(' ');
                      
                      fetch('/__console_log', {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                          type: method,
                          message: message,
                          timestamp: new Date().toISOString()
                        })
                      }).catch(e => {
                        // サーバーへの送信に失敗した場合は無視（無限ループを防ぐ）
                      });
                    } catch (e) {
                      // エラーがあっても無視
                    }
                  };
                }
                
                // 各コンソールメソッドをオーバーライド
                overrideConsole('log');
                overrideConsole('error');
                overrideConsole('warn');
                overrideConsole('info');
                
                // 未処理のエラーもキャプチャ
                window.addEventListener('error', function(event) {
                  const errorMsg = event.message + '\\n' + (event.error && event.error.stack || '');
                  console.error('[UNCAUGHT ERROR]', errorMsg);
                });
                
                console.log('Console redirection initialized - logs will be sent to the server');
              </script>
            `;
            
            // ヘッドタグの前にスクリプトを挿入
            return html.replace('</head>', script + '</head>');
          }
        },
        configureServer(server) {
          // コンソールログを受け取るエンドポイントを追加
          server.middlewares.use('/__console_log', (req, res) => {
            if (req.method === 'POST') {
              let body = '';
              req.on('data', chunk => {
                body += chunk.toString();
              });
              
              req.on('end', () => {
                try {
                  const data = JSON.parse(body);
                  const { type, message, timestamp } = data;
                  
                  // タイプ別にコンソール出力を変える
                  const prefix = `[BROWSER ${timestamp}]`;
                  switch (type) {
                    case 'error':
                      console.error(`${prefix} 🔴 ERROR: ${message}`);
                      break;
                    case 'warn':
                      console.warn(`${prefix} 🟠 WARN: ${message}`);
                      break;
                    case 'info':
                      console.info(`${prefix} 🔵 INFO: ${message}`);
                      break;
                    default:
                      console.log(`${prefix} 🟢 LOG: ${message}`);
                  }
                } catch (e) {
                  console.error('Failed to parse browser log:', e);
                }
                
                res.writeHead(200, { 'Content-Type': 'text/plain' });
                res.end('OK');
              });
            } else {
              res.writeHead(405);
              res.end('Method Not Allowed');
            }
          });
          
          console.log('Browser console redirection enabled - browser logs will be shown in the server terminal');
        }
      },
      // カスタムプラグイン：指定されたディレクトリをマウント
      {
        name: 'vite-plugin-custom-mount',
        configureServer(server) {
          // 各マウント設定に対してミドルウェアを設定
          for (const mount of mounts) {
            const sourcePath = mount.sourcePath;
            const targetPath = mount.targetPath;
            const filePattern = mount.filePattern || '*';
            
            server.middlewares.use(targetPath, (req, res, next) => {
              // リクエストパスを取得
              const reqPath = req.url || '';
              
              // ファイルパターンに一致するかチェック
              if (filePattern !== '*' && !reqPath.endsWith('/') && !reqPath.match(new RegExp(filePattern.replace('*', '.*')))) {
                return next();
              }
              
              // Denoのファイルシステムを使ってファイルを提供
              if (reqPath === '/') {
                // ディレクトリリストを提供
                try {
                  const files = Deno.readDirSync(sourcePath);
                  const fileList = Array.from(files)
                    .filter(entry => entry.isFile && (filePattern === '*' || entry.name.match(new RegExp(filePattern.replace('*', '.*')))))
                    .map(entry => entry.name);
                  
                  res.setHeader('Content-Type', 'application/json');
                  res.end(JSON.stringify(fileList));
                } catch (error) {
                  console.error(`ディレクトリ読み取りエラー ${sourcePath}:`, error);
                  res.statusCode = 500;
                  res.end(JSON.stringify({ error: `ディレクトリの読み取りに失敗しました: ${error.message}` }));
                }
              } else {
                // 個別のファイルを提供
                try {
                  const filePath = path.join(sourcePath, reqPath);
                  const content = Deno.readTextFileSync(filePath);
                  res.setHeader('Content-Type', 'text/plain');
                  res.end(content);
                } catch (error) {
                  console.error(`ファイル読み取りエラー ${path.join(sourcePath, reqPath)}:`, error);
                  res.statusCode = 404;
                  res.end(JSON.stringify({ error: `ファイルが見つかりません: ${error.message}` }));
                }
              }
            });
            
            console.log(`マウント完了: ${sourcePath} -> ${targetPath} (パターン: ${filePattern})`);
          }
        }
      }
    ],
    define: {
      'process.env.NODE_ENV': '\"development\"',
      'import.meta.env.DEV': 'true',
      // 環境変数としてマウント情報を追加
      'import.meta.env.KUZU_MOUNTS': JSON.stringify(mounts.map(m => ({ 
        source: m.sourcePath, 
        target: m.targetPath,
        pattern: m.filePattern
      }))),
    },
    resolve: {
      dedupe: ['react', 'react-dom'],
      alias: [
        { find: 'react', replacement: 'https://esm.sh/react@18.2.0' },
        { find: 'react-dom', replacement: 'https://esm.sh/react-dom@18.2.0' },
        { find: 'react-dom/client', replacement: 'https://esm.sh/react-dom@18.2.0/client' }
      ]
    },
    optimizeDeps: {
      force: true,
      // kuzu-wasmを除外リストに追加
      exclude: ['kuzu-wasm'],
      esbuildOptions: {
        supported: {
          'top-level-await': true
        }
      }
    },
    build: {
      rollupOptions: {
        external: [], // 外部化するモジュールを指定しない（空リスト）
      },
      target: 'esnext',
    },
    esbuild: {
      jsx: "automatic",
      jsxImportSource: "https://esm.sh/react@18.2.0"
    },
    server: {
      watch: {
        usePolling: true,
        interval: 100,
        // マウントしたディレクトリも監視対象に追加
        include: [
          "**/*.ts",
          "**/*.tsx",
          "**/*.js",
          "**/*.jsx",
          "**/*.json",
          "**/*.html",
          "**/*.css",
          ...mounts.map(m => `${m.sourcePath}/**/*`)
        ]
      },
      fs: {
        // Viteのファイルシステムアクセスを設定
        strict: false,
        allow: allowPaths,
      },
      headers: {
        // クロスオリジン分離の設定（SharedArrayBuffer対応に必須）
        'Cross-Origin-Embedder-Policy': 'require-corp',
        'Cross-Origin-Opener-Policy': 'same-origin'
      }
    }
  };

  return createServer(config);
}

// メイン関数
async function main() {
  console.log("KuzuDB ブラウザ - 開発サーバー起動");
  
  try {
    // コマンドライン引数の解析
    const { mounts } = parseCommandLineArgs();
    
    if (mounts.length === 0) {
      console.log("警告: マウント設定が指定されていません。デフォルトの public ディレクトリのみがマウントされます。");
      console.log("--mount オプションを使用してディレクトリをマウントすることができます。詳細は --help を参照してください。");
    } else {
      console.log(`${mounts.length} 個のディレクトリをマウント設定:`);
      for (const mount of mounts) {
        console.log(`  ${mount.sourcePath} -> ${mount.targetPath} (パターン: ${mount.filePattern || '*'})`);
      }
    }
    
    // 開発サーバーを起動
    const devServer = await createViteDevServer(mounts);
    await devServer.listen();
    console.log("サーバー起動完了");
    devServer.printUrls();
  } catch (error) {
    console.error("サーバー起動中にエラーが発生しました:", error.message);
    console.error("スタックトレース:", error.stack);
    Deno.exit(1);  // エラーコードと共に終了
  }
}

// スクリプトが直接実行された場合のみメイン関数を実行
if (import.meta.main) {
  await main();
}

// 関数をエクスポート
export { createViteDevServer, main, parseMountString };
