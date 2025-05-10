import { createServer } from "npm:vite";
import wasmPlugin from "npm:vite-plugin-wasm";
import topLevelAwait from "npm:vite-plugin-top-level-await";
import path from "node:path";
import { parse } from "https://deno.land/std@0.180.0/flags/mod.ts";

/**
 * コマンドライン引数を解析する
 * 
 * @returns 引数の解析結果
 */
function parseCommandLineArgs() {
  // 引数の解析
  const args = parse(Deno.args, {
    string: ["public", "query"],
    boolean: ["help"],
    alias: {
      "p": "public",
      "q": "query",
      "h": "help",
    },
  });

  // ヘルプの表示
  if (args.help) {
    console.log(`
KuzuDB ブラウザ - 開発サーバー

使用方法:
  deno run -A build.ts --public=PATH --query=PATH

必須オプション:
  --public=PATH, -p PATH   静的ファイルのパス（例: /home/nixos/bin/src/kuzu/browse/public）
  --query=PATH, -q PATH    KuzuDBクエリディレクトリのパス（例: /home/nixos/bin/src/kuzu/query）

その他のオプション:
  --help, -h              このヘルプメッセージを表示
`);
    Deno.exit(0);
  }

  // 必須オプションのチェック
  const errors = [];
  if (!args.public) {
    errors.push("エラー: --public オプションが指定されていません。静的ファイルのパス（例: /home/nixos/bin/src/kuzu/browse/public）を指定してください。");
  }
  if (!args.query) {
    errors.push("エラー: --query オプションが指定されていません。KuzuDBクエリディレクトリのパス（例: /home/nixos/bin/src/kuzu/query）を指定してください。");
  }

  // エラーがある場合
  if (errors.length > 0) {
    console.error(errors.join("\n"));
    console.error("\n詳細については --help オプションを指定して実行してください。");
    Deno.exit(1);
  }

  // パスの存在チェック
  for (const [name, dir] of Object.entries({ public: args.public, query: args.query })) {
    try {
      const stat = Deno.statSync(dir);
      if (!stat.isDirectory) {
        console.error(`エラー: ${name} パス "${dir}" はディレクトリではありません。`);
        Deno.exit(1);
      }
    } catch (e) {
      console.error(`エラー: ${name} パス "${dir}" が存在しないか、アクセスできません。`);
      Deno.exit(1);
    }
  }

  return args;
}

// 開発サーバーの起動
async function createViteDevServer(publicDir: string, queryDir: string) {
  // Vite設定
  const config = {
    configFile: false,
    root: ".",
    publicDir: publicDir, // 公開ディレクトリを指定
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
      // カスタムプラグイン：kuzuQueryパスの各ディレクトリをマウント
      {
        name: 'vite-plugin-kuzudb-query',
        configureServer(server) {
          // DDL, DML, DQL ディレクトリをマウント
          ['ddl', 'dml', 'dql'].forEach(dir => {
            const queryTypeDir = path.join(queryDir, dir);
            server.middlewares.use(`/${dir}`, (req, res, next) => {
              // リクエストパスを取得
              const reqPath = req.url || '';
              
              // .cypherファイルのみを許可
              if (!reqPath.endsWith('.cypher') && reqPath !== '/') {
                return next();
              }
              
              // Denoのファイルシステムを使ってファイルを提供
              if (reqPath === '/') {
                // ディレクトリリストを提供
                try {
                  const files = Deno.readDirSync(queryTypeDir);
                  const fileList = Array.from(files)
                    .filter(entry => entry.isFile && entry.name.endsWith('.cypher'))
                    .map(entry => entry.name);
                  
                  res.setHeader('Content-Type', 'application/json');
                  res.end(JSON.stringify(fileList));
                } catch (error) {
                  console.error(`ディレクトリ読み取りエラー ${queryTypeDir}:`, error);
                  res.statusCode = 500;
                  res.end(JSON.stringify({ error: `ディレクトリの読み取りに失敗しました: ${error.message}` }));
                }
              } else {
                // 個別のファイルを提供
                try {
                  const filePath = path.join(queryTypeDir, reqPath);
                  const content = Deno.readTextFileSync(filePath);
                  res.setHeader('Content-Type', 'text/plain');
                  res.end(content);
                } catch (error) {
                  console.error(`ファイル読み取りエラー ${path.join(queryTypeDir, reqPath)}:`, error);
                  res.statusCode = 404;
                  res.end(JSON.stringify({ error: `ファイルが見つかりません: ${error.message}` }));
                }
              }
            });
            
            console.log(`マウント完了: KuzuDBクエリディレクトリ ${queryTypeDir} -> /${dir}`);
          });
        }
      }
    ],
    define: {
      'process.env.NODE_ENV': '\"development\"',
      'import.meta.env.DEV': 'true',
      // 環境変数としてパスを追加
      'import.meta.env.KUZU_QUERY_PATH': JSON.stringify(queryDir),
      'import.meta.env.KUZU_PUBLIC_PATH': JSON.stringify(publicDir),
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
        // kuzu/queryディレクトリも監視対象に追加
        include: [
          "**/*.ts",
          "**/*.tsx",
          "**/*.js",
          "**/*.jsx",
          "**/*.json",
          "**/*.html",
          "**/*.css",
          `${queryDir}/**/*.cypher`
        ]
      },
      fs: {
        // Viteのファイルシステムアクセスを設定
        strict: false,
        allow: ['..', '.', '/', queryDir, publicDir],
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
    const args = parseCommandLineArgs();
    const publicDir = args.public;
    const queryDir = args.query;
    
    console.log(`公開ディレクトリ: ${publicDir}`);
    console.log(`クエリディレクトリ: ${queryDir}`);
    
    // 開発サーバーを起動
    const devServer = await createViteDevServer(publicDir, queryDir);
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
export { createViteDevServer, main };
