// 責務: サイトマップ生成バッチのデプロイ設定
// Uses: seo.sitemap.update, seo.index.notify
package sitemap_batch

import "capsules/index"

Uses: ["seo.sitemap.update", "seo.index.notify"]

DependsOn: {
  for u in Uses {
    "\(u)": {
      uri: u
      api: {
        requires: capsules_index.Caps[u].schema.req
      }
    }
  }
}
