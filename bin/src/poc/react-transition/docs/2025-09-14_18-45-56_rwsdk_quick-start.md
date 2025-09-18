# Quick Start

In this quick start you’ll go from zero to request/response in seconds and deploy to production in minutes!

Create a new project by running the following command, replacing `my-project-name` with your project name:

- [npm](#tab-panel-189)
- [pnpm](#tab-panel-190)
- [yarn](#tab-panel-191)

Terminal window ```
npx create-rwsdk my-project-name
```

Terminal window ```
pnpx create-rwsdk my-project-name
```

Terminal window ```
yarn dlx create-rwsdk my-project-name
```

## Start developing

[Section titled “Start developing”](#start-developing)

### Install the dependencies

[Section titled “Install the dependencies”](#install-the-dependencies)

```
cd my-project-name
```

- [npm](#tab-panel-192)
- [pnpm](#tab-panel-193)
- [yarn](#tab-panel-194)

Terminal window ```
npm install
```

Terminal window ```
pnpm install
```

Terminal window ```
yarn install
```

### Run the development server

[Section titled “Run the development server”](#run-the-development-server)

RedwoodSDK is just a plugin for Vite, so you can use the same commands to run the development server as you would with any other Vite project.

- [npm](#tab-panel-195)
- [pnpm](#tab-panel-196)
- [yarn](#tab-panel-197)

```
npm run dev
```

```
pnpm run dev
```

```
yarn run dev
```

```
VITE v6.2.0  ready in 500 ms
➜  Local:   http://localhost:5173/➜  Network: use --host to expose➜  press h + enter to show help
```

Access the development server in your browser, by default it’s available at [http://localhost:5173](http://localhost:5173),
where you should see “Hello World” displayed on the page.

![Hello World](/_astro/hello-world.BQtPD0ya_Z2agh3S.webp)

How exciting, your first request/response in RedwoodSDK!

### Your first route

[Section titled “Your first route”](#your-first-route)

The entry point of your webapp is `src/worker.tsx`, open that file in your favorite editor.

Here you’ll see the `defineApp` function, this is the main function that “defines your webapp,” where the purpose is to handle requests by returning responses to the client.

src/worker.tsx ```
import { defineApp } from "rwsdk/worker";import { route, render } from "rwsdk/router";
import { Document } from "@/app/Document";import { Home } from "@/app/pages/Home";
export default defineApp([  render(Document, [route("/", () => new Response("Hello, World!"))]),]);
```

You’re going to add your own route, insert the `"/ping"` route handler:

src/worker.tsx ```
import { defineApp } from "rwsdk/worker";import { route, render } from "rwsdk/router";
export default defineApp([  render(Document, [    route("/", () => new Response("Hello, World!")),    route("/ping", function () {      return <h1>Pong!</h1>;    }),  ]),]);
```

Now when you navigate to [http://localhost:5173/ping](http://localhost:5173/ping) you should see “Pong!” displayed on the page.

## Deploy to production

[Section titled “Deploy to production”](#deploy-to-production)

RedwoodSDK is built for the Cloudflare Development Platform. You can deploy your webapp to Cloudflare with a single command:

- [npm](#tab-panel-198)
- [pnpm](#tab-panel-199)
- [yarn](#tab-panel-200)

```
npm run release
```

```
pnpm run release
```

```
yarn run release
```

The first time you run the command it might fail and ask you to create a workers.dev subdomain. Do as indicated and go to the dashboard and open the
Workers menu. Opening the Workers landing page for the first time will create a workers.dev
subdomain automatically

[What's next?](/core/overview) Learn everything you need to know to build webapps with Redwood!
