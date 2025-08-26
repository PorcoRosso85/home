import{c as e}from"./chunk.uMdRCVvS.mjs";import{Fragment as t,jsx as n,jsxs as r}from"react/jsx-runtime";var i={};e(i,{default:()=>s,frontmatter:()=>a});const a=void 0;function o(e){let i={a:`a`,code:`code`,h1:`h1`,h2:`h2`,h3:`h3`,li:`li`,p:`p`,pre:`pre`,strong:`strong`,ul:`ul`,...e.components};return r(t,{children:[n(i.h1,{children:`@lazarv/react-server × Node 22`}),`
`,r(i.p,{children:[`React Server Components実装の`,n(i.code,{children:`@lazarv/react-server`}),`を Node.js 22 環境で動作検証するプロジェクト。`]}),`
`,n(i.h2,{children:`環境構築`}),`
`,n(i.h3,{children:`Nix Shell`}),`
`,n(i.pre,{children:n(i.code,{className:`language-bash`,children:`nix develop
`})}),`
`,n(i.p,{children:`Node.js 22およびpnpm環境が自動的にセットアップされます。`}),`
`,n(i.h2,{children:`セットアップ`}),`
`,n(i.pre,{children:n(i.code,{className:`language-bash`,children:`# 依存関係のインストール
pnpm install

# 開発サーバー起動
pnpm dev
`})}),`
`,n(i.h2,{children:`プロジェクト構造`}),`
`,n(i.pre,{children:n(i.code,{children:`├── app/           # アプリケーションコード
│   ├── page.tsx   # ページコンポーネント
│   └── layout.tsx # レイアウトコンポーネント
├── docs/          # ドキュメントキャッシュ
└── flake.nix      # Nix環境定義
`})}),`
`,n(i.h2,{children:`デプロイ`}),`
`,n(i.h3,{children:`Cloudflare Workers`}),`
`,n(i.pre,{children:n(i.code,{className:`language-bash`,children:`# ビルド
pnpm build

# Cloudflareへデプロイ
wrangler deploy
`})}),`
`,n(i.h2,{children:`技術スタック`}),`
`,r(i.ul,{children:[`
`,r(i.li,{children:[n(i.strong,{children:`Framework`}),`: @lazarv/react-server`]}),`
`,r(i.li,{children:[n(i.strong,{children:`Runtime`}),`: Node.js 22`]}),`
`,r(i.li,{children:[n(i.strong,{children:`Package Manager`}),`: pnpm`]}),`
`,r(i.li,{children:[n(i.strong,{children:`Environment`}),`: Nix Shell`]}),`
`,r(i.li,{children:[n(i.strong,{children:`Deployment`}),`: Cloudflare Workers`]}),`
`]}),`
`,n(i.h2,{children:`関連ドキュメント`}),`
`,r(i.ul,{children:[`
`,n(i.li,{children:n(i.a,{href:`docs/2025-08-26_17-18-18_react-server.dev_guide.md`,children:`React Server Guide`})}),`
`,n(i.li,{children:n(i.a,{href:`https://react-server.dev`,children:`@lazarv/react-server 公式`})}),`
`]}),`
`,n(i.h2,{children:`開発メモ`}),`
`,r(i.ul,{children:[`
`,n(i.li,{children:`React Server Components (RSC) のフレームワーク非依存実装`}),`
`,n(i.li,{children:`Vite互換のビルドシステム`}),`
`,n(i.li,{children:`ストリーミングSSRサポート`}),`
`,n(i.li,{children:`Server Functionsによるサーバー・クライアント間通信`}),`
`]})]})}function s(e={}){let{wrapper:t}=e.components||{};return t?n(t,{...e,children:n(o,{...e})}):o(e)}export{s as b,i as c,a as d};