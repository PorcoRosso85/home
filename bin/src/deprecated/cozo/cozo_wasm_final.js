#!/usr/bin/env -S nix run nixpkgs#nodejs_22 --

/**
 * CozoDBのWasm版を試すための最終デバッグサンプル
 */

// 必要なモジュールをインポート
const path = require('path');
const fs = require('fs');

// デバッグ情報収集関数
function collectDebugInfo() {
  const info = {
    nodeVersion: process.version,
    platform: process.platform,
    arch: process.arch,
    cwd: process.cwd(),
    env: {
      NODE_PATH: process.env.NODE_PATH,
      PATH: process.env.PATH
    }
  };
  
  console