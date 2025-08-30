# Next.js

**Start from CLI** - scaffold a Next.js project on Workers.

- [npm](#tab-panel-4065)
- [yarn](#tab-panel-4066)
- [pnpm](#tab-panel-4067)

Terminal window ```
npm create cloudflare@latest -- my-next-app --framework=next
```

Terminal window ```
yarn create cloudflare my-next-app --framework=next
```

Terminal window ```
pnpm create cloudflare@latest my-next-app --framework=next
```

This is a simple getting started guide. For detailed documentation on how to use the Cloudflare OpenNext adapter, visit the [OpenNext website ↗](https://opennext.js.org/cloudflare).

## What is Next.js?

[](#what-is-nextjs)

[Next.js ↗](https://nextjs.org/) is a [React ↗](https://react.dev/) framework for building full stack applications.

Next.js supports Server-side and Client-side rendering, as well as Partial Prerendering which lets you combine static and dynamic components in the same route.

You can deploy your Next.js app to Cloudflare Workers using the OpenNext adapter.

## Next.js supported features

[](#nextjs-supported-features)

Most Next.js features are supported by the Cloudflare OpenNext adapter:

| Feature | Cloudflare adapter | Notes |
| --- | --- | --- |
| App Router | 🟢 supported |  |
| Pages Router | 🟢 supported |  |
| Route Handlers | 🟢 supported |  |
| React Server Components | 🟢 supported |  |
| Static Site Generation (SSG) | 🟢 supported |  |
| Server-Side Rendering (SSR) | 🟢 supported |  |
| Incremental Static Regeneration (ISR) | 🟢 supported |  |
| Server Actions | 🟢 supported |  |
| Response streaming | 🟢 supported |  |
| asynchronous work with `next/after` | 🟢 supported |  |
| Middleware | 🟢 supported |  |
| Image optimization | 🟢 supported | Supported via [Cloudflare Images](/images/) |
| Partial Prerendering (PPR) | 🟢 supported | PPR is experimental in Next.js |
| Composable Caching ('use cache') | 🟢 supported | Composable Caching is experimental in Next.js |
| Node.js in Middleware | ⚪ not yet supported | Node.js middleware introduced in 15.2 are not yet supported |

## Deploy a new Next.js project on Workers

[](#deploy-a-new-nextjs-project-on-workers)

1. **Create a new project with the create-cloudflare CLI (C3).**

- [npm](#tab-panel-4068)
- [yarn](#tab-panel-4069)
- [pnpm](#tab-panel-4070)

Terminal window ```
npm create cloudflare@latest -- my-next-app --framework=next
```

Terminal window ```
yarn create cloudflare my-next-app --framework=next
```

Terminal window ```
pnpm create cloudflare@latest my-next-app --framework=next
```

What's happening behind the scenes?

When you run this command, C3 creates a new project directory, initiates
[Next.js's official setup tool ↗](https://nextjs.org/docs/app/api-reference/cli/create-next-app), and
configures the project for Cloudflare. It then offers the option to
instantly deploy your application to Cloudflare.
1. **Develop locally.**

After creating your project, run the following command in your project directory to start a local development server.
The command uses the Next.js development server. It offers the best developer experience by quickly reloading your app every time the source code is updated.

- [npm](#tab-panel-4071)
- [yarn](#tab-panel-4072)
- [pnpm](#tab-panel-4073)

Terminal window ```
npm run dev
```

Terminal window ```
yarn run dev
```

Terminal window ```
pnpm run dev
```
1. **Test and preview your site with the Cloudflare adapter.**

- [npm](#tab-panel-4074)
- [yarn](#tab-panel-4075)
- [pnpm](#tab-panel-4076)

Terminal window ```
npm run preview
```

Terminal window ```
yarn run preview
```

Terminal window ```
pnpm run preview
```

What's the difference between dev and preview?

The command used in the previous step uses the Next.js development server,
which runs in Node.js. However, your deployed application will run on
Cloudflare Workers, which uses the `workerd` runtime. Therefore when
running integration tests and previewing your application, you should use
the preview command, which is more accurate to production, as it executes
your application in the `workerd` runtime using `wrangler dev`.
1. **Deploy your project.**

You can deploy your project to a [`*.workers.dev` subdomain](/workers/configuration/routing/workers-dev/) or a [custom domain](/workers/configuration/routing/custom-domains/) from your local machine or any CI/CD system (including [Workers Builds](/workers/ci-cd/#workers-builds)). Use the following command to build and deploy. If you're using a CI service, be sure to update your "deploy command" accordingly.

- [npm](#tab-panel-4077)
- [yarn](#tab-panel-4078)
- [pnpm](#tab-panel-4079)

Terminal window ```
npm run deploy
```

Terminal window ```
yarn run deploy
```

Terminal window ```
pnpm run deploy
```

## Deploy an existing Next.js project on Workers

[](#deploy-an-existing-nextjs-project-on-workers)

You can convert an existing Next.js application to run on Cloudflare

1. **Install [`@opennextjs/cloudflare` ↗](https://www.npmjs.com/package/@opennextjs/cloudflare)**

- [npm](#tab-panel-4080)
- [yarn](#tab-panel-4081)
- [pnpm](#tab-panel-4082)

Terminal window ```
npm i @opennextjs/cloudflare@latest
```

Terminal window ```
yarn add @opennextjs/cloudflare@latest
```

Terminal window ```
pnpm add @opennextjs/cloudflare@latest
```
1. **Install [`wrangler CLI` ↗](https://developers.cloudflare.com/workers/wrangler) as a devDependency**

- [npm](#tab-panel-4083)
- [yarn](#tab-panel-4084)
- [pnpm](#tab-panel-4085)

Terminal window ```
npm i -D wrangler@latest
```

Terminal window ```
yarn add -D wrangler@latest
```

Terminal window ```
pnpm add -D wrangler@latest
```
1. **Add a Wrangler configuration file**

In your project root, create a [Wrangler configuration file](/workers/wrangler/configuration/) with the following content:

- [wrangler.jsonc](#tab-panel-4095)
- [wrangler.toml](#tab-panel-4096)

```
{  "main": ".open-next/worker.js",  "name": "my-app",  "compatibility_date": "2025-03-25",  "compatibility_flags": [    "nodejs_compat"  ],  "assets": {    "directory": ".open-next/assets",    "binding": "ASSETS"  }}
```

```
  main = ".open-next/worker.js"  name = "my-app"  compatibility_date = "2025-03-25"  compatibility_flags = ["nodejs_compat"]  [assets]  directory = ".open-next/assets"  binding = "ASSETS"
```
1. **Add a configuration file for OpenNext**

In your project root, create an OpenNext configuration file named `open-next.config.ts` with the following content:

```
import { defineCloudflareConfig } from "@opennextjs/cloudflare";
export default defineCloudflareConfig();
```
1. **Update `package.json`**

You can add the following scripts to your `package.json`:

```
"preview": "opennextjs-cloudflare build && opennextjs-cloudflare preview","deploy": "opennextjs-cloudflare build && opennextjs-cloudflare deploy","cf-typegen": "wrangler types --env-interface CloudflareEnv cloudflare-env.d.ts"
```

Usage

- `preview`: Builds your app and serves it locally, allowing you to
quickly preview your app running locally in the Workers runtime, via a
single command. - `deploy`: Builds your app, and then deploys it to
Cloudflare - `cf-typegen`: Generates a `cloudflare-env.d.ts` file at the
root of your project containing the types for the env.
1. **Develop locally.**

After creating your project, run the following command in your project directory to start a local development server.
The command uses the Next.js development server. It offers the best developer experience by quickly reloading your app after your source code is updated.

- [npm](#tab-panel-4086)
- [yarn](#tab-panel-4087)
- [pnpm](#tab-panel-4088)

Terminal window ```
npm run dev
```

Terminal window ```
yarn run dev
```

Terminal window ```
pnpm run dev
```
1. **Test your site with the Cloudflare adapter.**

The command used in the previous step uses the Next.js development server to offer a great developer experience.
However your application will run on Cloudflare Workers so you want to run your integration tests and verify that your application works correctly in this environment.

- [npm](#tab-panel-4089)
- [yarn](#tab-panel-4090)
- [pnpm](#tab-panel-4091)

Terminal window ```
npm run preview
```

Terminal window ```
yarn run preview
```

Terminal window ```
pnpm run preview
```
1. **Deploy your project.**

You can deploy your project to a [`*.workers.dev` subdomain](/workers/configuration/routing/workers-dev/) or a [custom domain](/workers/configuration/routing/custom-domains/) from your local machine or any CI/CD system (including [Workers Builds](/workers/ci-cd/#workers-builds)). Use the following command to build and deploy. If you're using a CI service, be sure to update your "deploy command" accordingly.

- [npm](#tab-panel-4092)
- [yarn](#tab-panel-4093)
- [pnpm](#tab-panel-4094)

Terminal window ```
npm run deploy
```

Terminal window ```
yarn run deploy
```

Terminal window ```
pnpm run deploy
```

## Was this helpful?

- **Resources**
- [API](/api/)
- [New to Cloudflare?](/fundamentals/)
- [Directory](/directory/)
- [Sponsorships](/sponsorships/)
- [Open Source](https://github.com/cloudflare)

- **Support**
- [Help Center](https://support.cloudflare.com/)
- [System Status](https://www.cloudflarestatus.com/)
- [Compliance](https://www.cloudflare.com/trust-hub/compliance-resources/)
- [GDPR](https://www.cloudflare.com/trust-hub/gdpr/)

- **Company**
- [cloudflare.com](https://www.cloudflare.com/)
- [Our team](https://www.cloudflare.com/people/)
- [Careers](https://www.cloudflare.com/careers/)

- **Tools**
- [Cloudflare Radar](https://radar.cloudflare.com/)
- [Speed Test](https://speed.cloudflare.com/)
- [Is BGP Safe Yet?](https://isbgpsafeyet.com/)
- [RPKI Toolkit](https://rpki.cloudflare.com/)
- [Certificate Transparency](https://ct.cloudflare.com/)

- **Community**
- [X](https://x.com/cloudflare)
- [Discord](http://discord.cloudflare.com/)
- [YouTube](https://www.youtube.com/cloudflare)
- [GitHub](https://github.com/cloudflare/cloudflare-docs)

- © 2025 Cloudflare, Inc.
- [Privacy Policy](https://www.cloudflare.com/privacypolicy/)
- [Terms of Use](https://www.cloudflare.com/website-terms/)
- [Report Security Issues](https://www.cloudflare.com/disclosure/)
- [Trademark](https://www.cloudflare.com/trademark/)
- ![privacy options](/_astro/privacyoptions.BWXSiJOZ_22PXh4.svg)
