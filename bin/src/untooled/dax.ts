#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-all
import $ from "jsr:@david/dax";

async function main() {
  const actionIndex = await $.select({
    message: "実行するアクションを選んでください",
    options: ["ファイルを作成", "Web サイトから情報を取得", "終了"],
  });

  switch (actionIndex) {
    case 0:
      await createFile();
      break;
    case 1:
      await fetchWebsiteInfo();
      break;
    case 2:
      $.logStep("終了します");
      break;
  }
}

async function createFile() {
  const fileName = await $.prompt("作成するファイル名を入力してください");
  const filePath = $.path(fileName);

  if (filePath.existsSync()) {
    $.logError(`ファイル ${fileName} は既に存在します`);
    return;
  }

  filePath.writeTextSync(`このファイルは dax CLI ツールによって作成されました。\n作成日時: ${new Date().toLocaleString()}`);
  $.logStep(`ファイル ${fileName} を作成しました`);
}

async function fetchWebsiteInfo() {
  const url = await $.prompt("Web サイトの URL を入力してください");
  try {
    const response = await $.request(url).text();
    $.logStep(`Web サイト ${url} の情報を取得しました`);
    //  console.log(response); //  取得した内容をコンソールに表示する場合はコメントアウトを外す
    $.logLight("（取得した内容はコンソール出力するにはコメントアウトを外してください）");
  } catch (error) {
    $.logError(`Web サイト ${url} の情報取得に失敗しました: ${error}`);
  }
}


await main();
