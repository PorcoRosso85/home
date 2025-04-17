#!/usr/bin/env -S nix run nixpkgs#nodejs_22 --

/**
 * Claude Desktop設定ビルダーツール - /home/nixos/.config/claudedesktop/claude_desktop_config.json を構築します
 * 
 * このツールは直接実行または require() で使用できます。
 * 直接実行時: ./claude_config_builder.js --config_dir=<dir> --output_file=<file> [--dry_run] [--no-backup]
 * @typedef {Object} Args
 * @property {string} [config_dir="/home/nixos/bin/src/mcp_servers_extended"] - MCP設定ファイルが保存されているディレクトリ
 * @property {string} [output_file="/home/nixos/.config/claudedesktop/claude_desktop_config.json"] - 出力する設定ファイルパス
 * @property {boolean} [dry_run=false] - 実際の変更なしで実行結果のみ表示
 * @property {boolean} [backup=true] - 既存の設定ファイルをバックアップする
 * @param {Args} args
 */
exports.run = function (args) {
  const fs = require('fs');
  const path = require('path');

  // デフォルト値を設定
  const configDir = args.config_dir || "/home/nixos/bin/src/mcp_servers_extended";
  const outputFile = args.output_file || "/home/nixos/.config/claudedesktop/claude_desktop_config.json";
  const dryRun = args.dry_run || false;
  const makeBackup = args.backup !== false; // デフォルトはtrue

  // ディレクトリが存在するか確認
  if (!fs.existsSync(configDir)) {
    return `エラー: 設定ディレクトリ ${configDir} が見つかりません。`;
  }

  // 既存の設定ファイルをバックアップ
  if (fs.existsSync(outputFile) && makeBackup && !dryRun) {
    const backupFile = `${outputFile}.backup.${new Date().toISOString().replace(/:/g, '-')}`;
    fs.copyFileSync(outputFile, backupFile);
    console.log(`既存設定のバックアップを作成しました: ${backupFile}`);
  }

  // 有効なMCP設定ファイルを読み込む (disabledディレクトリを除く)
  const mcpServers = {};
  const files = fs.readdirSync(configDir);
  
  for (const file of files) {
    const filePath = path.join(configDir, file);
    // ディレクトリは処理しない (disabledディレクトリなど)
    if (fs.statSync(filePath).isDirectory()) {
      continue;
    }
    
    // JSONファイルのみ処理
    if (path.extname(file) === '.json') {
      try {
        const configData = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        // ファイル名から拡張子を除いたものをキーとして使用
        const serverName = path.basename(file, '.json');
        mcpServers[serverName] = configData;
        console.log(`設定ファイル ${file} を読み込みました`);
      } catch (error) {
        console.error(`エラー: ${file} の解析に失敗しました: ${error.message}`);
      }
    }
  }

  // 最終的な設定ファイルオブジェクトを構築
  const configObject = {
    mcpServers: mcpServers
  };

  // 結果を表示
  console.log('\n最終設定:');
  console.log(JSON.stringify(configObject, null, 2));

  // dry-runモードでない場合は設定を保存
  if (!dryRun) {
    fs.writeFileSync(outputFile, JSON.stringify(configObject, null, 2));
    console.log(`\n設定ファイルを保存しました: ${outputFile}`);
  } else {
    console.log('\ndry-runモードのため、設定は保存されていません');
  }

  return `Claude Desktop設定ビルダーが正常に完了しました${dryRun ? ' (dry-run)' : ''}`;
}

// スクリプトが直接実行された場合の処理
if (require.main === module) {
  const args = {};
  // コマンドライン引数の解析
  process.argv.slice(2).forEach(arg => {
    if (arg.startsWith('--config_dir=')) {
      args.config_dir = arg.substring('--config_dir='.length);
    } 
    else if (arg.startsWith('--output_file=')) {
      args.output_file = arg.substring('--output_file='.length);
    }
    else if (arg === '--dry_run' || arg === '--dry-run') {
      args.dry_run = true;
    }
    else if (arg === '--no-backup') {
      args.backup = false;
    }
  });

  // 実行結果を表示
  const result = exports.run(args);
  console.log(`\n${result}`);
}
