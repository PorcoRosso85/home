// 責務: UGC投稿機能の提供
// 提供URI: ugc.post.create, ugc.post.read, ugc.post.list
package ugc_post

provides: {
  "ugc.post.create": {
    schema: {
      req: { /* TODO */ }
      res: { /* TODO */ }
    }
    caps: ["write"]
  }
  "ugc.post.read": {
    schema: {
      req: { /* TODO */ }
      res: { /* TODO */ }
    }
    caps: ["read"]
  }
  "ugc.post.list": {
    schema: {
      req: { /* TODO */ }
      res: { /* TODO */ }
    }
    caps: ["read"]
  }
}
