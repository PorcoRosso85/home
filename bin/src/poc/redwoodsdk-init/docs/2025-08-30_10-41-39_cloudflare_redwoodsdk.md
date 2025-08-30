# RedwoodSDK

In this guide, you will create a new [RedwoodSDK ↗](https://rwsdk.com/) application and deploy it to Cloudflare Workers.

RedwoodSDK is a composable framework for building server-side web apps on Cloudflare. It starts as a Vite plugin that unlocks SSR, React Server Components, Server Functions, and realtime capabilities.

## Deploy a new RedwoodSDK application on Workers

[](#deploy-a-new-redwoodsdk-application-on-workers)

1. **Create a new project.**

Run the following command, replacing `< project-name>` with your desired project name:

- [npm](#tab-panel-4123)
- [yarn](#tab-panel-4124)
- [pnpm](#tab-panel-4125)

Terminal window ```
npx degit redwoodjs/sdk/starters/standard#main <project-name>
```

Terminal window ```
yarn dlx degit redwoodjs/sdk/starters/standard#main <project-name>
```

Terminal window ```
pnpx degit redwoodjs/sdk/starters/standard#main <project-name>
```
1. **Change the directory.**

Terminal window ```
cd <project-name>
```
1. **Install dependencies.**

- [npm](#tab-panel-4126)
- [yarn](#tab-panel-4127)
- [pnpm](#tab-panel-4128)

Terminal window ```
npm install
```

Terminal window ```
yarn install
```

Terminal window ```
pnpm install
```
1. **Develop locally.**

Run the following command in the project directory to start a local development server. RedwoodSDK is just a plugin for Vite, so you can use the same dev workflow as any other Vite project:

- [npm](#tab-panel-4129)
- [yarn](#tab-panel-4130)
- [pnpm](#tab-panel-4131)

Terminal window ```
npm run dev
```

Terminal window ```
yarn run dev
```

Terminal window ```
pnpm run dev
```
1. **Deploy your project.**

You can deploy your project to a `*.workers.dev` subdomain or a [Custom Domain](/workers/configuration/routing/custom-domains/), either from your local machine or from any CI/CD system, including [Cloudflare Workers CI/CD](/workers/ci-cd/builds/).

Use the following command to build and deploy. If you are using CI, make sure to update your [deploy command](/workers/ci-cd/builds/configuration/#build-settings) configuration accordingly.

- [npm](#tab-panel-4132)
- [yarn](#tab-panel-4133)
- [pnpm](#tab-panel-4134)

Terminal window ```
npm run release
```

Terminal window ```
yarn run release
```

Terminal window ```
pnpm run release
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
