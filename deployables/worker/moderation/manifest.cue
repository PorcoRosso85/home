// 責務: モデレーションワーカーのデプロイ設定
// Uses: ugc.moderation.check, ugc.post.create
package moderation_worker

import "capsules/index"

Uses: ["ugc.moderation.check", "ugc.post.create"]

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
