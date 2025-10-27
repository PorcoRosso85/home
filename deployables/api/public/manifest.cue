// 責務: パブリックAPIのデプロイ設定
// Uses: ugc.post.create, ugc.post.read, media.image.upload
package public_api

import "capsules/index"

Uses: ["ugc.post.create", "ugc.post.read", "media.image.upload"]

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
