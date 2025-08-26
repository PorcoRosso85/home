import{c as e}from"./chunk.uMdRCVvS.mjs";import{Fragment as t,jsx as n,jsxs as r}from"react/jsx-runtime";var i={};e(i,{default:()=>s,frontmatter:()=>a});const a={url:`https://react-server.dev/deploy/adapters#adapters-in-development`,saved_at:`2025-08-26T17:26:26Z`,title:`Adapters - Deploy - @lazarv/react-server`,domain:`react-server.dev`};function o(e){let i={a:`a`,code:`code`,li:`li`,p:`p`,pre:`pre`,ul:`ul`,...e.components};return r(t,{children:[r(i.p,{children:[n(i.a,{href:`/deploy`,children:`Deploy →`}),` `,n(i.a,{href:`https://github.com/lazarv/react-server/edit/main/docs/src/pages/en/(pages)/deploy/adapters.mdx`,children:`Edit this page`}),` # Adapters`]}),`
`,n(i.p,{children:`You can use adapters to configure your app for different deployment environments. This is a list of available adapters and how to configure them.`}),`
`,r(i.ul,{children:[`
`,r(i.li,{children:[`
`,r(i.p,{children:[n(i.code,{children:`@lazarv/react-server-adapter-vercel`}),` for Vercel deployment`]}),`
`]}),`
`,r(i.li,{children:[`
`,r(i.p,{children:[n(i.code,{children:`@lazarv/react-server-adapter-netlify`}),` for Netlify deployment`]}),`
`]}),`
`,r(i.li,{children:[`
`,r(i.p,{children:[n(i.code,{children:`@lazarv/react-server-adapter-cloudflare-pages`}),` for Cloudflare Pages deployment`]}),`
`]}),`
`,r(i.li,{children:[`
`,r(i.p,{children:[n(i.code,{children:`@lazarv/react-server-adapter-cloudflare-workers`}),` for Cloudflare Workers deployment`]}),`
`]}),`
`,r(i.li,{children:[`
`,r(i.p,{children:[n(i.code,{children:`@lazarv/react-server-adapter-sst`}),` for Serverless Stack deployment`]}),`
`]}),`
`]}),`
`,r(i.p,{children:[`Add `,n(i.code,{children:`adapter`}),` entry to your `,n(i.code,{children:`react-server.config.mjs`}),` file. You can specify the name of the adapter as a string. The adapter package will be resolved from your project ' s dependencies.`]}),`
`,n(i.pre,{children:n(i.code,{className:`language-mjs`,children:`export default {
  adapter: '@lazarv/react-server-adapter-vercel',
};
\`\`\` You can also specify custom options for all adapters. Configuration options are different for each adapter. Check the page of the adapter for details.

\`\`\`mjs
export default {
  adapter: [
    '@lazarv/react-server-adapter-vercel',
    {
      // Custom options
    },
  ],
};
\`\`\` You can also import an adapter from a package or file.

\`\`\`mjs
import adapter from '@lazarv/react-server-adapter-vercel';

export default {
  adapter: adapter({
    // Custom options
  }),
};
\`\`\` [← Router: Configuration](/router/configuration) [Deploy: Vercel →](/deploy/vercel)
`})})]})}function s(e={}){let{wrapper:t}=e.components||{};return t?n(t,{...e,children:n(o,{...e})}):o(e)}export{s as b,i as c,a as d};