// 責務: PSEO定期生成ジョブのデプロイ設定
// Uses: seo.pseo.generate
package generate_pseo_cron

import "capsules/index"

Uses: ["seo.pseo.generate"]

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
