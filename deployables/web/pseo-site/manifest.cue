// 責務: PSEOサイトのデプロイ設定
// Uses: seo.pseo.generate, ugc.post.read
package pseo_site

import "capsules/index"

Uses: ["seo.pseo.generate", "ugc.post.read"]

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
