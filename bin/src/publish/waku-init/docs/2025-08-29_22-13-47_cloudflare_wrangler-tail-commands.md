# Commands

Wrangler offers a number of commands to manage your Cloudflare Workers.

- [`docs`](#docs) - Open this page in your default browser.
- [`init`](#init) - Create a new project from a variety of web frameworks and templates.
- [`containers`](#containers) - Interact with Containers.
- [`d1`](#d1) - Interact with D1.
- [`vectorize`](#vectorize) - Interact with Vectorize indexes.
- [`hyperdrive`](#hyperdrive) - Manage your Hyperdrives.
- [`deploy`](#deploy) - Deploy your Worker to Cloudflare.
- [`dev`](#dev) - Start a local server for developing your Worker.
- [`delete`](#delete) - Delete your Worker from Cloudflare.
- [`kv namespace`](#kv-namespace) - Manage Workers KV namespaces.
- [`kv key`](#kv-key) - Manage key-value pairs within a Workers KV namespace.
- [`kv bulk`](#kv-bulk) - Manage multiple key-value pairs within a Workers KV namespace in batches.
- [`r2 bucket`](#r2-bucket) - Manage Workers R2 buckets.
- [`r2 object`](#r2-object) - Manage Workers R2 objects.
- [`secret`](#secret) - Manage the secret variables for a Worker.
- [`secret bulk`](#secret-bulk) - Manage multiple secret variables for a Worker.
- [`secrets-store secret`](#secrets-store-secret) - Manage account secrets within a secrets store.
- [`secrets-store store`](#secrets-store-store) - Manage your store within secrets store.
- [`workflows`](#workflows) - Manage and configure Workflows.
- [`tail`](#tail) - Start a session to livestream logs from a deployed Worker.
- [`pages`](#pages) - Configure Cloudflare Pages.
- [`pipelines`](#pipelines) - Configure Cloudflare Pipelines.
- [`queues`](#queues) - Configure Workers Queues.
- [`login`](#login) - Authorize Wrangler with your Cloudflare account using OAuth.
- [`logout`](#logout) - Remove Wrangler’s authorization for accessing your account.
- [`whoami`](#whoami) - Retrieve your user information and test your authentication configuration.
- [`versions`](#versions) - Retrieve details for recent versions.
- [`deployments`](#deployments) - Retrieve details for recent deployments.
- [`rollback`](#rollback) - Rollback to a recent deployment.
- [`dispatch-namespace`](#dispatch-namespace) - Interact with a [dispatch namespace](/cloudflare-for-platforms/workers-for-platforms/reference/how-workers-for-platforms-works/#dispatch-namespace).
- [`mtls-certificate`](#mtls-certificate) - Manage certificates used for mTLS connections.
- [`cert`](#cert) - Manage certificates used for mTLS and Certificate Authority (CA) chain connections.
- [`types`](#types) - Generate types from bindings and module rules in configuration.
- [`telemetry`](#telemetry) - Configure whether Wrangler can collect anonymous usage data.
- [`check`](#check) - Validate your Worker.

---

## How to run Wrangler commands

[](#how-to-run-wrangler-commands)

This page provides a reference for Wrangler commands.

```
wrangler <COMMAND> <SUBCOMMAND> [PARAMETERS] [OPTIONS]
```

Since Cloudflare recommends [installing Wrangler locally](/workers/wrangler/install-and-update/) in your project(rather than globally), the way to run Wrangler will depend on your specific setup and package manager.

- [npm](#tab-panel-2774)
- [yarn](#tab-panel-2775)
- [pnpm](#tab-panel-2776)

Terminal window ```
npx wrangler <COMMAND> <SUBCOMMAND> [PARAMETERS] [OPTIONS]
```

Terminal window ```
yarn wrangler <COMMAND> <SUBCOMMAND> [PARAMETERS] [OPTIONS]
```

Terminal window ```
pnpm wrangler <COMMAND> <SUBCOMMAND> [PARAMETERS] [OPTIONS]
```

You can add Wrangler commands that you use often as scripts in your project's `package.json` file:

```
{  ...  "scripts": {    "deploy": "wrangler deploy",    "dev": "wrangler dev"  }  ...}
```

You can then run them using your package manager of choice:

- [npm](#tab-panel-2777)
- [yarn](#tab-panel-2778)
- [pnpm](#tab-panel-2779)

Terminal window ```
npm run deploy
```

Terminal window ```
yarn run deploy
```

Terminal window ```
pnpm run deploy
```

---

## `docs`

[](#docs)

Open the Cloudflare developer documentation in your default browser.

```
wrangler docs [<COMMAND>]
```

- `COMMAND` string optional
  - The Wrangler command you want to learn more about. This opens your default browser to the section of the documentation that describes the command.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

## `init`

[](#init)

Create a new project via the [create-cloudflare-cli (C3) tool](/workers/get-started/guide/#1-create-a-new-worker-project). A variety of web frameworks are available to choose from as well as templates. Dependencies are installed by default, with the option to deploy your project immediately.

```
wrangler init [<NAME>] [OPTIONS]
```

- `NAME` string optional (default: name of working directory)
  - The name of the Workers project. This is both the directory name and `name` property in the generated [Wrangler configuration](/workers/wrangler/configuration/).
- `--yes` boolean optional
  - Answer yes to any prompts for new projects.
- `--from-dash` string optional
  - Fetch a Worker initialized from the dashboard. This is done by passing the flag and the Worker name. `wrangler init --from-dash < WORKER_NAME>`.
  - The `--from-dash` command will not automatically sync changes made to the dashboard after the command is used. Therefore, it is recommended that you continue using the CLI.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## `containers`

[](#containers)

Interact with Cloudflare's Container Platform.

### `build`

[](#containers-build)

Build a Container image from a Dockerfile.

```
wrangler containers build [PATH] [OPTIONS]
```

- `PATH` string optional
  - Path for the directory containing the Dockerfile to build.
- `-t, --tag` string required
  - Name and optionally a tag (format: "name:tag").
- `--path-to-docker` string optional
  - Path to your docker binary if it's not on `$PATH`.
  - Default: "docker"
- `-p, --push` boolean optional
  - Push the built image to Cloudflare's managed registry.
  - Default: false

### `delete`

[](#containers-delete)

Delete a Container (application).

```
wrangler containers delete <CONTAINER_ID> [OPTIONS]
```

- `CONTAINER_ID` string required
  - The ID of the Container to delete.

### `images`

[](#containers-images)

Perform operations on images in your containers registry.

#### `images list`

[](#containers-images-list)

List images in your containers registry.

```
wrangler containers images list [OPTIONS]
```

- `--filter` string optional
  - Regex to filter results.
- `--json` boolean optional
  - Return output as clean JSON.
  - Default: false

#### `images delete`

[](#containers-images-delete)

Remove an image from your containers registry.

```
wrangler containers images delete [IMAGE] [OPTIONS]
```

- `IMAGE` string required
  - Image to delete of the form `IMAGE:TAG`

### `info`

[](#containers-info)

Get information about a specific Container, including top-level details and a list of instances.

```
wrangler containers info <CONTAINER_ID> [OPTIONS]
```

- `CONTAINER_ID` string required
  - The ID of the Container to get information about.

### `list`

[](#containers-list)

List the Containers in your account.

```
wrangler containers list [OPTIONS]
```

### `push`

[](#containers-push)

Push a tagged image to a Cloudflare managed registry, which is automatically integrated with your account.

```
wrangler containers push [TAG] [OPTIONS]
```

- `TAG` string required
  - The name and tag of the container image to push.
- `--path-to-docker` string optional
  - Path to your docker binary if it's not on `$PATH`.
  - Default: "docker"

## `d1`

[](#d1)

Interact with Cloudflare's D1 service.

### `create`

[](#d1-create)

Creates a new D1 database, and provides the binding and UUID that you will put in your Wrangler file.

```
wrangler d1 create <DATABASE_NAME> [OPTIONS]
```

- `DATABASE_NAME` string required
  - The name of the new D1 database.
- `--location` string optional
  - Provide an optional [location hint](/d1/configuration/data-location/) for your database leader.
  - Available options include `weur` (Western Europe), `eeur` (Eastern Europe), `apac` (Asia Pacific), `oc` (Oceania), `wnam` (Western North America), and `enam` (Eastern North America).

### `info`

[](#d1-info)

Get information about a D1 database, including the current database size and state.

```
wrangler d1 info <DATABASE_NAME> [OPTIONS]
```

- `DATABASE_NAME` string required
  - The name of the D1 database to get information about.
- `--json` boolean optional
  - Return output as JSON rather than a table.

### `list`

[](#d1-list)

List all D1 databases in your account.

```
wrangler d1 list [OPTIONS]
```

- `--json` boolean optional
  - Return output as JSON rather than a table.

### `delete`

[](#d1-delete)

Delete a D1 database.

```
wrangler d1 delete <DATABASE_NAME> [OPTIONS]
```

- `DATABASE_NAME` string required
  - The name of the D1 database to delete.
- `-y, --skip-confirmation` boolean optional
  - Skip deletion confirmation prompt.

### `execute`

[](#d1-execute)

Execute a query on a D1 database.

```
wrangler d1 execute <DATABASE_NAME> [OPTIONS]
```

- `DATABASE_NAME` string required
  - The name of the D1 database to execute a query on.
- `--command` string optional
  - The SQL query you wish to execute.
- `--file` string optional
  - Path to the SQL file you wish to execute.
- `-y, --yes` boolean optional
  - Answer `yes` to any prompts.
- `--local` boolean (default: true) optional
  - Execute commands/files against a local database for use with [wrangler dev](/workers/wrangler/commands/#dev).
- `--remote` boolean (default: false) optional
  - Execute commands/files against a remote D1 database for use with [wrangler dev --remote](/workers/wrangler/commands/#dev).
- `--persist-to` string optional
  - Specify directory to use for local persistence (for use in combination with `--local`).
- `--json` boolean optional
  - Return output as JSON rather than a table.
- `--preview` boolean optional
  - Execute commands/files against a preview D1 database (as defined by `preview_database_id` in the [Wrangler configuration file](/workers/wrangler/configuration/#d1-databases)).

### `export`

[](#d1-export)

Export a D1 database or table's schema and/or content to a `.sql` file.

```
wrangler d1 export <DATABASE_NAME> [OPTIONS]
```

- `DATABASE_NAME` string required
  - The name of the D1 database to export.
- `--local` boolean (default: true) optional
  - Export from a local database for use with [wrangler dev](/workers/wrangler/commands/#dev).
- `--remote` boolean (default: false) optional
  - Export from a remote D1 database for use with [wrangler dev --remote](/workers/wrangler/commands/#dev).
- `--output` string required
  - Path to the SQL file for your export.
- `--table` string optional
  - The name of the table within a D1 database to export.
- `--no-data` boolean (default: false) optional
  - Controls whether export SQL file contains database data. Note that `--no-data=true` is not recommended due to a known wrangler limitation that intreprets the value as false.
- `--no-schema` boolean (default: false) optional
  - Controls whether export SQL file contains database schema. Note that `--no-schema=true` is not recommended due to a known wrangler limitation that intreprets the value as false.

### `time-travel restore`

[](#d1-time-travel-restore)

Restore a database to a specific point-in-time using [Time Travel](/d1/reference/time-travel/).

```
wrangler d1 time-travel restore <DATABASE_NAME> [OPTIONS]
```

- `DATABASE_NAME` string required
  - The name of the D1 database to execute a query on.
- `--bookmark` string optional
  - A D1 bookmark representing the state of a database at a specific point in time.
- `--timestamp` string optional
  - A UNIX timestamp or JavaScript date-time `string` within the last 30 days.
- `--json` boolean optional
  - Return output as JSON rather than a table.

### `time-travel info`

[](#d1-time-travel-info)

Inspect the current state of a database for a specific point-in-time using [Time Travel](/d1/reference/time-travel/).

```
wrangler d1 time-travel info <DATABASE_NAME> [OPTIONS]
```

- `DATABASE_NAME` string required
  - The name of the D1 database to execute a query on.
- `--timestamp` string optional
  - A UNIX timestamp or JavaScript date-time `string` within the last 30 days.
- `--json` b boolean optional
  - Return output as JSON rather than a table.

### `migrations create`

[](#d1-migrations-create)

Create a new migration.

This will generate a new versioned file inside the `migrations` folder. Name your migration file as a description of your change. This will make it easier for you to find your migration in the `migrations` folder. An example filename looks like:

`0000_create_user_table.sql`

The filename will include a version number and the migration name you specify below.

```
wrangler d1 migrations create <DATABASE_NAME> <MIGRATION_NAME>
```

- `DATABASE_NAME` string required
  - The name of the D1 database you wish to create a migration for.
- `MIGRATION_NAME` string required
  - A descriptive name for the migration you wish to create.

### `migrations list`

[](#d1-migrations-list)

View a list of unapplied migration files.

```
wrangler d1 migrations list <DATABASE_NAME> [OPTIONS]
```

- `DATABASE_NAME` string required
  - The name of the D1 database you wish to list unapplied migrations for.
- `--local` boolean optional
  - Show the list of unapplied migration files on your locally persisted D1 database.
- `--remote` boolean (default: false) optional
  - Show the list of unapplied migration files on your remote D1 database.
- `--persist-to` string optional
  - Specify directory to use for local persistence (for use in combination with `--local`).
- `--preview` boolean optional
  - Show the list of unapplied migration files on your preview D1 database (as defined by `preview_database_id` in the [Wrangler configuration file](/workers/wrangler/configuration/#d1-databases)).

### `migrations apply`

[](#d1-migrations-apply)

Apply any unapplied migrations.

This command will prompt you to confirm the migrations you are about to apply. Confirm that you would like to proceed. After, a backup will be captured.

The progress of each migration will be printed in the console.

When running the apply command in a CI/CD environment or another non-interactive command line, the confirmation step will be skipped, but the backup will still be captured.

If applying a migration results in an error, this migration will be rolled back, and the previous successful migration will remain applied.

```
wrangler d1 migrations apply <DATABASE_NAME> [OPTIONS]
```

- `DATABASE_NAME` string required
  - The name of the D1 database you wish to apply your migrations on.
- `--env` string optional
  - Specify which environment configuration to use for D1 binding
- `--local` boolean (default: true) optional
  - Execute any unapplied migrations on your locally persisted D1 database.
- `--remote` boolean (default: false) optional
  - Execute any unapplied migrations on your remote D1 database.
- `--persist-to` string optional
  - Specify directory to use for local persistence (for use in combination with `--local`).
- `--preview` boolean optional
  - Execute any unapplied migrations on your preview D1 database (as defined by `preview_database_id` in the [Wrangler configuration file](/workers/wrangler/configuration/#d1-databases)).

---

## `hyperdrive`

[](#hyperdrive)

Manage [Hyperdrive](/hyperdrive/) database configurations.

## hyperdrive create

[](#hyperdrive-create)

- [npm](#tab-panel-2815)
- [pnpm](#tab-panel-2816)
- [yarn](#tab-panel-2817)

Terminal window ```
npx wrangler hyperdrive create [NAME]
```

Terminal window ```
pnpm wrangler hyperdrive create [NAME]
```

Terminal window ```
yarn wrangler hyperdrive create [NAME]
```

- `--name` string required The name of the Hyperdrive config
- `--connection-string` string The connection string for the database you want Hyperdrive to connect to - ex: protocol://user:password@host:port/database
- `--origin-host` string alias: --host The host of the origin database
- `--origin-port` number alias: --port The port number of the origin database
- `--origin-scheme` string alias: --scheme default: postgresql The scheme used to connect to the origin database
- `--database` string The name of the database within the origin database
- `--origin-user` string alias: --user The username used to connect to the origin database
- `--origin-password` string alias: --password The password used to connect to the origin database
- `--access-client-id` string The Client ID of the Access token to use when connecting to the origin database
- `--access-client-secret` string The Client Secret of the Access token to use when connecting to the origin database
- `--caching-disabled` boolean Disables the caching of SQL responses
- `--max-age` number Specifies max duration for which items should persist in the cache, cannot be set when caching is disabled
- `--swr` number Indicates the number of seconds cache may serve the response after it becomes stale, cannot be set when caching is disabled
- `--ca-certificate-id` string alias: --ca-certificate-uuid Sets custom CA certificate when connecting to origin database. Must be valid UUID of already uploaded CA certificate.
- `--mtls-certificate-id` string alias: --mtls-certificate-uuid Sets custom mTLS client certificates when connecting to origin database. Must be valid UUID of already uploaded public/private key certificates.
- `--sslmode` string Sets CA sslmode for connecting to database.
- `--origin-connection-limit` number The (soft) maximum number of connections that Hyperdrive may establish to the origin database

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## hyperdrive update

[](#hyperdrive-update)

- [npm](#tab-panel-2818)
- [pnpm](#tab-panel-2819)
- [yarn](#tab-panel-2820)

Terminal window ```
npx wrangler hyperdrive update [ID]
```

Terminal window ```
pnpm wrangler hyperdrive update [ID]
```

Terminal window ```
yarn wrangler hyperdrive update [ID]
```

- `--id` string required The ID of the Hyperdrive config
- `--name` string Give your config a new name
- `--connection-string` string The connection string for the database you want Hyperdrive to connect to - ex: protocol://user:password@host:port/database
- `--origin-host` string alias: --host The host of the origin database
- `--origin-port` number alias: --port The port number of the origin database
- `--origin-scheme` string alias: --scheme The scheme used to connect to the origin database
- `--database` string The name of the database within the origin database
- `--origin-user` string alias: --user The username used to connect to the origin database
- `--origin-password` string alias: --password The password used to connect to the origin database
- `--access-client-id` string The Client ID of the Access token to use when connecting to the origin database
- `--access-client-secret` string The Client Secret of the Access token to use when connecting to the origin database
- `--caching-disabled` boolean Disables the caching of SQL responses
- `--max-age` number Specifies max duration for which items should persist in the cache, cannot be set when caching is disabled
- `--swr` number Indicates the number of seconds cache may serve the response after it becomes stale, cannot be set when caching is disabled
- `--ca-certificate-id` string alias: --ca-certificate-uuid Sets custom CA certificate when connecting to origin database. Must be valid UUID of already uploaded CA certificate.
- `--mtls-certificate-id` string alias: --mtls-certificate-uuid Sets custom mTLS client certificates when connecting to origin database. Must be valid UUID of already uploaded public/private key certificates.
- `--sslmode` string Sets CA sslmode for connecting to database.
- `--origin-connection-limit` number The (soft) maximum number of connections that Hyperdrive may establish to the origin database

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## hyperdrive list

[](#hyperdrive-list)

- [npm](#tab-panel-2821)
- [pnpm](#tab-panel-2822)
- [yarn](#tab-panel-2823)

Terminal window ```
npx wrangler hyperdrive list
```

Terminal window ```
pnpm wrangler hyperdrive list
```

Terminal window ```
yarn wrangler hyperdrive list
```

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## hyperdrive delete

[](#hyperdrive-delete)

- [npm](#tab-panel-2824)
- [pnpm](#tab-panel-2825)
- [yarn](#tab-panel-2826)

Terminal window ```
npx wrangler hyperdrive delete [ID]
```

Terminal window ```
pnpm wrangler hyperdrive delete [ID]
```

Terminal window ```
yarn wrangler hyperdrive delete [ID]
```

- `--id` string required The ID of the Hyperdrive config

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## hyperdrive get

[](#hyperdrive-get)

- [npm](#tab-panel-2827)
- [pnpm](#tab-panel-2828)
- [yarn](#tab-panel-2829)

Terminal window ```
npx wrangler hyperdrive get [ID]
```

Terminal window ```
pnpm wrangler hyperdrive get [ID]
```

Terminal window ```
yarn wrangler hyperdrive get [ID]
```

- `--id` string required The ID of the Hyperdrive config

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

---

## `vectorize`

[](#vectorize)

Interact with a [Vectorize](/vectorize/) vector database.

### `create`

[](#vectorize-create)

Creates a new vector index, and provides the binding and name that you will put in your Wrangler file.

Terminal window ```
npx wrangler vectorize create <INDEX_NAME> [--dimensions=<NUM_DIMENSIONS>] [--metric=<DISTANCE_METRIC>] [--description=<DESCRIPTION>]
```

- `INDEX_NAME` string required
  - The name of the new index to create. Must be unique for an account and cannot be changed after creation.
- `--dimensions` number required
  - The vector dimension width to configure the index for. Cannot be changed after creation.
- `--metric` string required
  - The distance metric to use for calculating vector distance. Must be one of `cosine`, `euclidean`, or `dot-product`.
- `--description` string optional
  - A description for your index.
- `--deprecated-v1` boolean optional
  - Create a legacy Vectorize index. Please note that legacy Vectorize indexes are on a [deprecation path](/vectorize/reference/transition-vectorize-legacy).

### `list`

[](#vectorize-list)

List all Vectorize indexes in your account, including the configured dimensions and distance metric.

Terminal window ```
npx wrangler vectorize list
```

- `--deprecated-v1` boolean optional
  - List legacy Vectorize indexes. Please note that legacy Vectorize indexes are on a [deprecation path](/vectorize/reference/transition-vectorize-legacy).

### `get`

[](#vectorize-get)

Get details about an individual index, including its configuration.

Terminal window ```
npx wrangler vectorize get <INDEX_NAME>
```

- `INDEX_NAME` string required
  - The name of the index to fetch details for.
- `--deprecated-v1` boolean optional
  - Get a legacy Vectorize index. Please note that legacy Vectorize indexes are on a [deprecation path](/vectorize/reference/transition-vectorize-legacy).

### `info`

[](#vectorize-info)

Get some additional information about an individual index, including the vector count and details about the last processed mutation.

Terminal window ```
npx wrangler vectorize info <INDEX_NAME>
```

- `INDEX_NAME` string required
  - The name of the index to fetch details for.

### `delete`

[](#vectorize-delete)

Delete a Vectorize index.

Terminal window ```
npx wrangler vectorize delete <INDEX_NAME> [OPTIONS]
```

- `INDEX_NAME` string required
  - The name of the Vectorize index to delete.
- `--force` boolean optional
  - Skip confirmation when deleting the index (Note: This is not a recoverable operation).
- `--deprecated-v1` boolean optional
  - Delete a legacy Vectorize index. Please note that legacy Vectorize indexes are on a [deprecation path](/vectorize/reference/transition-vectorize-legacy).

### `insert`

[](#vectorize-insert)

Insert vectors into an index.

Terminal window ```
npx wrangler vectorize insert <INDEX_NAME> [OPTIONS]
```

- `INDEX_NAME` string required
  - The name of the Vectorize index to upsert vectors in.
- `--file` string required
  - A file containing the vectors to insert in newline-delimited JSON (JSON) format.
- `--batch-size` number optional
  - The number of vectors to insert at a time (default: `1000`).
- `--deprecated-v1` boolean optional
  - Insert into a legacy Vectorize index. Please note that legacy Vectorize indexes are on a [deprecation path](/vectorize/reference/transition-vectorize-legacy).

### `upsert`

[](#vectorize-upsert)

Upsert vectors into an index. Existing vectors in the index would be overwritten.

Terminal window ```
npx wrangler vectorize upsert <INDEX_NAME> [OPTIONS]
```

- `INDEX_NAME` string required
  - The name of the Vectorize index to upsert vectors in.
- `--file` string required
  - A file containing the vectors to insert in newline-delimited JSON (JSON) format.
- `--batch-size` number optional
  - The number of vectors to insert at a time (default: `5000`).

### `query`

[](#vectorize-query)

Query a Vectorize index for similar vectors.

Terminal window ```
npx wrangler vectorize query <INDEX_NAME> [OPTIONS]
```

- `INDEX_NAME` string required
  - The name of the Vectorize index to query.
- `--vector` array optional
  - Vector against which the Vectorize index is queried. Either this or the `vector-id` param must be provided.
- `--vector-id` string optional
  - Identifier for a vector that is already present in the index against which the index is queried. Either this or the `vector` param must be provided.
- `--top-k` number optional
  - The number of vectors to query (default: `5`).
- `--return-values` boolean optional
  - Enable to return vector values in the response (default: `false`).
- `--return-metadata` string optional
  - Enable to return vector metadata in the response. Must be one of `none`, `indexed`, or `all` (default: `none`).
- `--namespace` string optional
  - Query response to only include vectors from this namespace.
- `--filter` string optional
  - Filter vectors based on this metadata filter. Example: `'{ 'p1': 'abc', 'p2': { '$ne': true }, 'p3': 10, 'p4': false, 'nested.p5': 'abcd' }'`

### `list-vectors`

[](#vectorize-list-vectors)

List vector identifiers in a Vectorize index in a paginated manner.

Terminal window ```
npx wrangler vectorize list-vectors <INDEX_NAME> [OPTIONS]
```

- `INDEX_NAME` string required
  - The name of the Vectorize index from which vector identifiers need to be listed.
- `--count` number optional
  - Number of vector IDs to return per page. Must be between 1 and 1000 (default: `100`).
- `--cursor` string optional
  - Pagination cursor from the previous response to continue listing from that position.

### `get-vectors`

[](#vectorize-get-vectors)

Fetch vectors from a Vectorize index using the provided ids.

Terminal window ```
npx wrangler vectorize get-vectors <INDEX_NAME> [OPTIONS]
```

- `INDEX_NAME` string required
  - The name of the Vectorize index from which vectors need to be fetched.
- `--ids` array required
  - List of ids for which vectors must be fetched.

### `delete-vectors`

[](#vectorize-delete-vectors)

Delete vectors in a Vectorize index using the provided ids.

Terminal window ```
npx wrangler vectorize delete-vectors <INDEX_NAME> [OPTIONS]
```

- `INDEX_NAME` string required
  - The name of the Vectorize index from which vectors need to be deleted.
- `--ids` array required
  - List of ids corresponding to the vectors that must be deleted.

### `create-metadata-index`

[](#vectorize-create-metadata-index)

Enable metadata filtering on the specified property.

Terminal window ```
npx wrangler vectorize create-metadata-index <INDEX_NAME> [OPTIONS]
```

- `INDEX_NAME` string required
  - The name of the Vectorize index for which metadata index needs to be created.
- `--property-name` string required
  - Metadata property for which metadata filtering should be enabled.
- `--type` string required
  - Data type of the property. Must be one of `string`, `number`, or `boolean`.

### `list-metadata-index`

[](#vectorize-list-metadata-index)

List metadata properties on which metadata filtering is enabled.

Terminal window ```
npx wrangler vectorize list-metadata-index <INDEX_NAME> [OPTIONS]
```

- `INDEX_NAME` string required
  - The name of the Vectorize index for which metadata indexes needs to be fetched.

### `delete-metadata-index`

[](#vectorize-delete-metadata-index)

Disable metadata filtering on the specified property.

Terminal window ```
npx wrangler vectorize delete-metadata-index <INDEX_NAME> [OPTIONS]
```

- `INDEX_NAME` string required
  - The name of the Vectorize index for which metadata index needs to be disabled.
- `--property-name` string required
  - Metadata property for which metadata filtering should be disabled.

---

## `dev`

[](#dev)

Start a local server for developing your Worker.

```
wrangler dev [<SCRIPT>] [OPTIONS]
```

- `SCRIPT` string
  - The path to an entry point for your Worker. Only required if your [Wrangler configuration file](/workers/wrangler/configuration/) does not include a `main` key (for example, `main = "index.js"`).
- `--name` string optional
  - Name of the Worker.
- `--config`, `-c` string\[\] optional
  - Path(s) to [Wrangler configuration file](/workers/wrangler/configuration/). If not provided, Wrangler will use the nearest config file based on your current working directory.
  - You can provide multiple configuration files to run multiple Workers in one dev session like this: `wrangler dev -c ./wrangler.toml -c ../other-worker/wrangler.toml`. The first config will be treated as the *primary* Worker, which will be exposed over HTTP. The remaining config files will only be accessible via a service binding from the primary Worker.
- `--no-bundle` boolean (default: false) optional
  - Skip Wrangler's build steps. Particularly useful when using custom builds. Refer to [Bundling ↗](https://developers.cloudflare.com/workers/wrangler/bundling/) for more information.
- `--env` string optional
  - Perform on a specific environment.
- `--compatibility-date` string optional
  - A date in the form yyyy-mm-dd, which will be used to determine which version of the Workers runtime is used.
- `--compatibility-flags`, `--compatibility-flag` string\[\] optional
  - Flags to use for compatibility checks.
- `--latest` boolean (default: true) optional
  - Use the latest version of the Workers runtime.
- `--ip` string optional
  - IP address to listen on, defaults to `localhost`.
- `--port` number optional
  - Port to listen on.
- `--inspector-port` number optional
  - Port for devtools to connect to.
- `--routes`, `--route` string\[\] optional
  - Routes to upload.
  - For example: `--route example.com/*`.
- `--host` string optional
  - Host to forward requests to, defaults to the zone of project.
- `--local-protocol` ' http ' | ' https ' (default: http) optional
  - Protocol to listen to requests on.
- `--https-key-path` string optional
  - Path to a custom certificate key.
- `--https-cert-path` string optional
  - Path to a custom certificate.
- `--local-upstream` string optional
  - Host to act as origin in local mode, defaults to `dev.host` or route.
- `--assets` string optional beta
  - Folder of static assets to be served. Replaces [Workers Sites](/workers/configuration/sites/). Visit [assets](/workers/static-assets/) for more information.
- `--site` string optional deprecated, use \`--assets\`
  - Folder of static assets for Workers Sites.
- `--site-include` string\[\] optional deprecated
  - Array of `.gitignore` -style patterns that match file or directory names from the sites directory. Only matched items will be uploaded.
- `--site-exclude` string\[\] optional deprecated
  - Array of `.gitignore` -style patterns that match file or directory names from the sites directory. Matched items will not be uploaded.
- `--upstream-protocol` ' http ' | ' https ' (default: https) optional
  - Protocol to forward requests to host on.
- `--var` key:value\\\[\] optional
  - Array of `key:value` pairs to inject as variables into your code. The value will always be passed as a string to your Worker.
  - For example, `--var "git_hash:'$(git rev-parse HEAD)'" "test:123"` makes the `git_hash` and `test` variables available in your Worker's `env`.
  - This flag is an alternative to defining [`vars`](/workers/wrangler/configuration/#non-inheritable-keys) in your [Wrangler configuration file](/workers/wrangler/configuration/). If defined in both places, this flag's values will be used.
- `--define` key:value\\\[\] optional
  - Array of `key:value` pairs to replace global identifiers in your code.
  - For example, `--define "GIT_HASH:'$(git rev-parse HEAD)'"` will replace all uses of `GIT_HASH` with the actual value at build time.
  - This flag is an alternative to defining [`define`](/workers/wrangler/configuration/#non-inheritable-keys) in your [Wrangler configuration file](/workers/wrangler/configuration/). If defined in both places, this flag's values will be used.
- `--tsconfig` string optional
  - Path to a custom `tsconfig.json` file.
- `--minify` boolean optional
  - Minify the Worker.
- `--persist-to` string optional
  - Specify directory to use for local persistence.
- `--remote` boolean (default: false) optional
  - Develop against remote resources and data stored on Cloudflare's network.
- `--test-scheduled` boolean (default: false) optional
  - Exposes a `/__scheduled` fetch route which will trigger a scheduled event (Cron Trigger) for testing during development. To simulate different cron patterns, a `cron` query parameter can be passed in: `/__scheduled?cron=*+*+*+*+*` or `/cdn-cgi/handler/scheduled?cron=*+*+*+*+*`.
- `--log-level` ' debug ' | ' info ' | ' log ' | ' warn ' | ' error| ' none ' (default: log) optional
  - Specify Wrangler's logging level.
- `--show-interactive-dev-session` boolean (default: true if the terminal supports interactivity) optional
  - Show the interactive dev session.
- `--alias` `Array < string>`
  - Specify modules to alias using [module aliasing](/workers/wrangler/configuration/#module-aliasing).

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

`wrangler dev` is a way to [locally test](/workers/development-testing/) your Worker while developing. With `wrangler dev` running, send HTTP requests to `localhost:8787` and your Worker should execute as expected. You will also see `console.log` messages and exceptions appearing in your terminal.

---

## `deploy`

[](#deploy)

Deploy your Worker to Cloudflare.

```
wrangler deploy [<SCRIPT>] [OPTIONS]
```

- `SCRIPT` string
  - The path to an entry point for your Worker. Only required if your [Wrangler configuration file](/workers/wrangler/configuration/) does not include a `main` key (for example, `main = "index.js"`).
- `--name` string optional
  - Name of the Worker.
- `--no-bundle` boolean (default: false) optional
  - Skip Wrangler's build steps. Particularly useful when using custom builds. Refer to [Bundling ↗](https://developers.cloudflare.com/workers/wrangler/bundling/) for more information.
- `--env` string optional
  - Perform on a specific environment.
- `--outdir` string optional
  - Path to directory where Wrangler will write the bundled Worker files.
- `--compatibility-date` string optional
  - A date in the form yyyy-mm-dd, which will be used to determine which version of the Workers runtime is used.
- `--compatibility-flags`, `--compatibility-flag` string\[\] optional
  - Flags to use for compatibility checks.
- `--latest` boolean (default: true) optional
  - Use the latest version of the Workers runtime.
- `--assets` string optional beta
  - Folder of static assets to be served. Replaces [Workers Sites](/workers/configuration/sites/). Visit [assets](/workers/static-assets/) for more information.
- `--site` string optional deprecated, use \`--assets\`
  - Folder of static assets for Workers Sites.
- `--site-include` string\[\] optional deprecated
  - Array of `.gitignore` -style patterns that match file or directory names from the sites directory. Only matched items will be uploaded.
- `--site-exclude` string\[\] optional deprecated
  - Array of `.gitignore` -style patterns that match file or directory names from the sites directory. Matched items will not be uploaded.
- `--var` key:value\\\[\] optional
  - Array of `key:value` pairs to inject as variables into your code. The value will always be passed as a string to your Worker.
  - For example, `--var git_hash:$(git rev-parse HEAD) test:123` makes the `git_hash` and `test` variables available in your Worker's `env`.
  - This flag is an alternative to defining [`vars`](/workers/wrangler/configuration/#non-inheritable-keys) in your [Wrangler configuration file](/workers/wrangler/configuration/). If defined in both places, this flag's values will be used.
- `--define` key:value\\\[\] optional
  - Array of `key:value` pairs to replace global identifiers in your code.
  - For example, `--define GIT_HASH:$(git rev-parse HEAD)` will replace all uses of `GIT_HASH` with the actual value at build time.
  - This flag is an alternative to defining [`define`](/workers/wrangler/configuration/#non-inheritable-keys) in your [Wrangler configuration file](/workers/wrangler/configuration/). If defined in both places, this flag's values will be used.
- `--triggers`, `--schedule`, `--schedules` string\[\] optional
  - Cron schedules to attach to the deployed Worker. Refer to [Cron Trigger Examples](/workers/configuration/cron-triggers/#examples).
- `--routes`, `--route` string\[\] optional
  - Routes where this Worker will be deployed.
  - For example: `--route example.com/*`.
- `--tsconfig` string optional
  - Path to a custom `tsconfig.json` file.
- `--minify` boolean optional
  - Minify the bundled Worker before deploying.
- `--dry-run` boolean (default: false) optional
  - Compile a project without actually deploying to live servers. Combined with `--outdir`, this is also useful for testing the output of `npx wrangler deploy`. It also gives developers a chance to upload our generated sourcemap to a service like Sentry, so that errors from the Worker can be mapped against source code, but before the service goes live.
- `--keep-vars` boolean (default: false) optional
  - It is recommended best practice to treat your Wrangler developer environment as a source of truth for your Worker configuration, and avoid making changes via the Cloudflare dashboard.
  - If you change your environment variables in the Cloudflare dashboard, Wrangler will override them the next time you deploy. If you want to disable this behaviour set `keep-vars` to `true`.
  - Secrets are never deleted by a deployment whether this flag is true or false.
- `--dispatch-namespace` string optional
  - Specify the [Workers for Platforms dispatch namespace](/cloudflare-for-platforms/workers-for-platforms/get-started/configuration/#2-create-a-dispatch-namespace) to upload this Worker to.
- `--metafile` string optional
  - Specify a file to write the build metadata from esbuild to. If flag is used without a path string, this defaults to `bundle-meta.json` inside the directory specified by `--outdir`. This can be useful for understanding the bundle size.
- `--containers-rollout` immediate | gradual optional
  - Specify the [rollout strategy](/containers/faq#how-do-container-updates-and-rollouts-work) for [Containers](/containers) associated with the Worker. If set to `immediate`, 100% of container instances will be updated in one rollout step, overriding any configuration in `rollout_step_percentage`. Note that `rollout_active_grace_period`, if configured, still applies.
  - Defaults to `gradual`, where the default rollout is 10% then 100% of instances.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## `delete`

[](#delete)

Delete your Worker and all associated Cloudflare developer platform resources.

```
wrangler delete [<SCRIPT>] [OPTIONS]
```

- `SCRIPT` string
  - The path to an entry point for your Worker. Only required if your [Wrangler configuration file](/workers/wrangler/configuration/) does not include a `main` key (for example, `main = "index.js"`).
- `--name` string optional
  - Name of the Worker.
- `--env` string optional
  - Perform on a specific environment.
- `--dry-run` boolean (default: false) optional
  - Do not actually delete the Worker. This is useful for testing the output of `wrangler delete`.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## `kv namespace`

[](#kv-namespace)

Manage Workers KV namespaces.

## kv namespace create

[](#kv-namespace-create)

- [npm](#tab-panel-2782)
- [pnpm](#tab-panel-2783)
- [yarn](#tab-panel-2784)

Terminal window ```
npx wrangler kv namespace create [NAMESPACE]
```

Terminal window ```
pnpm wrangler kv namespace create [NAMESPACE]
```

Terminal window ```
yarn wrangler kv namespace create [NAMESPACE]
```

- `--namespace` string required The name of the new namespace
- `--preview` boolean Interact with a preview namespace

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## kv namespace list

[](#kv-namespace-list)

- [npm](#tab-panel-2785)
- [pnpm](#tab-panel-2786)
- [yarn](#tab-panel-2787)

Terminal window ```
npx wrangler kv namespace list
```

Terminal window ```
pnpm wrangler kv namespace list
```

Terminal window ```
yarn wrangler kv namespace list
```

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## kv namespace delete

[](#kv-namespace-delete)

- [npm](#tab-panel-2788)
- [pnpm](#tab-panel-2789)
- [yarn](#tab-panel-2790)

Terminal window ```
npx wrangler kv namespace delete
```

Terminal window ```
pnpm wrangler kv namespace delete
```

Terminal window ```
yarn wrangler kv namespace delete
```

- `--binding` string The binding name to the namespace to delete from
- `--namespace-id` string The id of the namespace to delete
- `--preview` boolean Interact with a preview namespace

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## kv namespace rename

[](#kv-namespace-rename)

- [npm](#tab-panel-2791)
- [pnpm](#tab-panel-2792)
- [yarn](#tab-panel-2793)

Terminal window ```
npx wrangler kv namespace rename [OLD-NAME]
```

Terminal window ```
pnpm wrangler kv namespace rename [OLD-NAME]
```

Terminal window ```
yarn wrangler kv namespace rename [OLD-NAME]
```

- `--old-name` string The current name (title) of the namespace to rename
- `--namespace-id` string The id of the namespace to rename
- `--new-name` string required The new name for the namespace

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## `kv key`

[](#kv-key)

Manage key-value pairs within a Workers KV namespace.

## kv key put

[](#kv-key-put)

- [npm](#tab-panel-2794)
- [pnpm](#tab-panel-2795)
- [yarn](#tab-panel-2796)

Terminal window ```
npx wrangler kv key put [KEY] [VALUE]
```

Terminal window ```
pnpm wrangler kv key put [KEY] [VALUE]
```

Terminal window ```
yarn wrangler kv key put [KEY] [VALUE]
```

- `--key` string required The key to write to
- `--value` string The value to write
- `--binding` string The binding name to the namespace to write to
- `--namespace-id` string The id of the namespace to write to
- `--preview` boolean Interact with a preview namespace
- `--ttl` number Time for which the entries should be visible
- `--expiration` number Time since the UNIX epoch after which the entry expires
- `--metadata` string Arbitrary JSON that is associated with a key
- `--path` string Read value from the file at a given path
- `--local` boolean Interact with local storage
- `--remote` boolean Interact with remote storage
- `--persist-to` string Directory for local persistence

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## kv key list

[](#kv-key-list)

- [npm](#tab-panel-2797)
- [pnpm](#tab-panel-2798)
- [yarn](#tab-panel-2799)

Terminal window ```
npx wrangler kv key list
```

Terminal window ```
pnpm wrangler kv key list
```

Terminal window ```
yarn wrangler kv key list
```

- `--binding` string The binding name to the namespace to list
- `--namespace-id` string The id of the namespace to list
- `--preview` boolean default: false Interact with a preview namespace
- `--prefix` string A prefix to filter listed keys
- `--local` boolean Interact with local storage
- `--remote` boolean Interact with remote storage
- `--persist-to` string Directory for local persistence

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## kv key get

[](#kv-key-get)

- [npm](#tab-panel-2800)
- [pnpm](#tab-panel-2801)
- [yarn](#tab-panel-2802)

Terminal window ```
npx wrangler kv key get [KEY]
```

Terminal window ```
pnpm wrangler kv key get [KEY]
```

Terminal window ```
yarn wrangler kv key get [KEY]
```

- `--key` string required The key value to get.
- `--binding` string The binding name to the namespace to get from
- `--namespace-id` string The id of the namespace to get from
- `--preview` boolean default: false Interact with a preview namespace
- `--text` boolean default: false Decode the returned value as a utf8 string
- `--local` boolean Interact with local storage
- `--remote` boolean Interact with remote storage
- `--persist-to` string Directory for local persistence

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## kv key delete

[](#kv-key-delete)

- [npm](#tab-panel-2803)
- [pnpm](#tab-panel-2804)
- [yarn](#tab-panel-2805)

Terminal window ```
npx wrangler kv key delete [KEY]
```

Terminal window ```
pnpm wrangler kv key delete [KEY]
```

Terminal window ```
yarn wrangler kv key delete [KEY]
```

- `--key` string required The key value to delete.
- `--binding` string The binding name to the namespace to delete from
- `--namespace-id` string The id of the namespace to delete from
- `--preview` boolean Interact with a preview namespace
- `--local` boolean Interact with local storage
- `--remote` boolean Interact with remote storage
- `--persist-to` string Directory for local persistence

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## `kv bulk`

[](#kv-bulk)

Manage multiple key-value pairs within a Workers KV namespace in batches.

## kv bulk get

[](#kv-bulk-get)

- [npm](#tab-panel-2806)
- [pnpm](#tab-panel-2807)
- [yarn](#tab-panel-2808)

Terminal window ```
npx wrangler kv bulk get [FILENAME]
```

Terminal window ```
pnpm wrangler kv bulk get [FILENAME]
```

Terminal window ```
yarn wrangler kv bulk get [FILENAME]
```

- `--filename` string required The file containing the keys to get
- `--binding` string The binding name to the namespace to get from
- `--namespace-id` string The id of the namespace to get from
- `--preview` boolean Interact with a preview namespace
- `--local` boolean Interact with local storage
- `--remote` boolean Interact with remote storage
- `--persist-to` string Directory for local persistence

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## kv bulk put

[](#kv-bulk-put)

- [npm](#tab-panel-2809)
- [pnpm](#tab-panel-2810)
- [yarn](#tab-panel-2811)

Terminal window ```
npx wrangler kv bulk put [FILENAME]
```

Terminal window ```
pnpm wrangler kv bulk put [FILENAME]
```

Terminal window ```
yarn wrangler kv bulk put [FILENAME]
```

- `--filename` string required The file containing the key/value pairs to write
- `--binding` string The binding name to the namespace to write to
- `--namespace-id` string The id of the namespace to write to
- `--preview` boolean Interact with a preview namespace
- `--ttl` number Time for which the entries should be visible
- `--expiration` number Time since the UNIX epoch after which the entry expires
- `--metadata` string Arbitrary JSON that is associated with a key
- `--local` boolean Interact with local storage
- `--remote` boolean Interact with remote storage
- `--persist-to` string Directory for local persistence

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## kv bulk delete

[](#kv-bulk-delete)

- [npm](#tab-panel-2812)
- [pnpm](#tab-panel-2813)
- [yarn](#tab-panel-2814)

Terminal window ```
npx wrangler kv bulk delete [FILENAME]
```

Terminal window ```
pnpm wrangler kv bulk delete [FILENAME]
```

Terminal window ```
yarn wrangler kv bulk delete [FILENAME]
```

- `--filename` string required The file containing the keys to delete
- `--binding` string The binding name to the namespace to delete from
- `--namespace-id` string The id of the namespace to delete from
- `--preview` boolean Interact with a preview namespace
- `--force` boolean alias: --f Do not ask for confirmation before deleting
- `--local` boolean Interact with local storage
- `--remote` boolean Interact with remote storage
- `--persist-to` string Directory for local persistence

Global flags

- `--v` boolean alias: --version Show version number
- `--cwd` string Run as if Wrangler was started in the specified directory instead of the current working directory
- `--config` string alias: --c Path to Wrangler configuration file
- `--env` string alias: --e Environment to use for operations, and for selecting .env and .dev.vars files
- `--env-file` string Path to an .env file to load - can be specified multiple times - values from earlier files are overridden by values in later files
- `--experimental-remote-bindings` boolean aliases: --x-remote-bindings Experimental: Enable Remote Bindings
- `--experimental-provision` boolean aliases: --x-provision Experimental: Enable automatic resource provisioning

## Global flags

[](#global-flags)

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## `r2 bucket`

[](#r2-bucket)

Interact with buckets in an R2 store.

### `create`

[](#r2-bucket-create)

Create a new R2 bucket.

```
wrangler r2 bucket create <NAME>
```

- `NAME` string required
  - The name of the new R2 bucket.
- `--location` string optional
  - The optional [location hint](/r2/reference/data-location/#location-hints) that determines geographic placement of the R2 bucket.
- `--storage-class` ' Standard|InfrequentAccess ' optional
  - The default storage class for objects uploaded to the bucket.
- `--jurisdiction` string optional
  - The jurisdiction where the R2 bucket is created. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).

### `info`

[](#r2-bucket-info)

Get information about an R2 bucket, including the bucket size and number of objects.

```
wrangler r2 bucket info <NAME>
```

- `NAME` string required
  - The name of the R2 bucket to get information about.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- `--json` boolean optional
  - Return output as clean JSON.
  - Default: false

### `delete`

[](#r2-bucket-delete)

Delete an R2 bucket.

```
wrangler r2 bucket delete <NAME>
```

- `NAME` string required
  - The name of the R2 bucket to delete.

### `list`

[](#r2-bucket-list)

List R2 bucket in the current account.

```
wrangler r2 bucket list
```

### `catalog enable`

[](#r2-bucket-catalog-enable)

Enable [R2 Data Catalog](/r2/data-catalog/) on an R2 bucket.

```
wrangler r2 bucket catalog enable <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the bucket to enable R2 Data Catalog for.

### `catalog disable`

[](#r2-bucket-catalog-disable)

Disable [R2 Data Catalog](/r2/data-catalog/) on an R2 bucket.

```
wrangler r2 bucket catalog disable <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the bucket to disable R2 Data Catalog for.

### `catalog get`

[](#r2-bucket-catalog-get)

Get the status of [R2 Data Catalog](/r2/data-catalog/) for an R2 bucket, including catalog URI and warehouse name.

```
wrangler r2 bucket catalog get <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket whose data catalog status to retrieve.

### `cors set`

[](#r2-bucket-cors-set)

Set the [CORS configuration](/r2/buckets/cors/) for an R2 bucket from a JSON file.

```
wrangler r2 bucket cors set <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to set the CORS configuration for.
- `--file` string required
  - Path to the JSON file containing CORS configuration (file must be in format of request body of [put bucket CORS policy API](/api/operations/r2-put-bucket-cors-policy)).
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- `--force` boolean optional
  - Skip confirmation when setting CORS configuration.

### `cors delete`

[](#r2-bucket-cors-delete)

Clear the [CORS configuration](/r2/buckets/cors/) for an R2 bucket.

```
wrangler r2 bucket cors delete <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to delete the CORS configuration for.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- `--force` boolean optional
  - Skip confirmation when clearing the CORS configuration.

### `cors list`

[](#r2-bucket-cors-list)

List the [CORS configuration](/r2/buckets/cors/) rules for an R2 bucket.

```
wrangler r2 bucket cors list <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to list the CORS rules for.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).

### `dev-url enable`

[](#r2-bucket-dev-url-enable)

Enable public access via the [r2.dev URL](/r2/buckets/public-buckets/#enable-managed-public-access) for an R2 bucket.

```
wrangler r2 bucket dev-url enable <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to enable public access via its r2.dev URL.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- `--force` boolean optional
  - Skip confirmation when enabling public access via r2.dev URL.

### `dev-url disable`

[](#r2-bucket-dev-url-disable)

Disable public access via the [r2.dev URL](/r2/buckets/public-buckets/#enable-managed-public-access) for an R2 bucket.

```
wrangler r2 bucket dev-url disable <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to disable public access via its r2.dev URL.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- `--force` boolean optional
  - Skip confirmation when disabling public access via r2.dev URL.

### `dev-url get`

[](#r2-bucket-dev-url-get)

Get the [r2.dev URL](/r2/buckets/public-buckets/#enable-managed-public-access) and status for an R2 bucket.

```
wrangler r2 bucket dev-url get <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket whose r2.dev URL status to retrieve.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).

### `domain add`

[](#r2-bucket-domain-add)

Connect a [custom domain](/r2/buckets/public-buckets/#custom-domains) to an R2 bucket.

```
wrangler r2 bucket domain add <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to connect a custom domain to.
- `--domain` string required
  - The custom domain to connect to the R2 bucket.
- `--zone-id` string required
  - The [zone ID](/fundamentals/account/find-account-and-zone-ids/) associated with the custom domain.
- `--min-tls` ' 1.0 ' | ' 1.1 ' | ' 1.2 ' | ' 1.3 ' optional
  - Set the minimum TLS version for the custom domain (defaults to 1.0 if not set).
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- `--force` boolean optional
  - Skip confirmation when adding the custom domain.

### `domain remove`

[](#r2-bucket-domain-remove)

Remove a [custom domain](/r2/buckets/public-buckets/#custom-domains) from an R2 bucket.

```
wrangler r2 bucket domain remove <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to remove the custom domain from.
- `--domain` string required
  - The custom domain to remove from the R2 bucket.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- `--force` boolean optional
  - Skip confirmation when removing the custom domain.

### `domain update`

[](#r2-bucket-domain-update)

Update settings for a [custom domain](/r2/buckets/public-buckets/#custom-domains) connected to an R2 bucket.

```
wrangler r2 bucket domain update <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket associated with the custom domain to update.
- `--domain` string required
  - The custom domain whose settings will be updated.
- `--min-tls` ' 1.0 ' | ' 1.1 ' | ' 1.2 ' | ' 1.3 ' optional
  - Update the minimum TLS version for the custom domain.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).

### `domain get`

[](#r2-bucket-domain-get)

Get [custom domain](/r2/buckets/public-buckets/#custom-domains) connected to an R2 bucket.

```
wrangler r2 bucket domain get <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket whose custom domain to retrieve.
- `--domain` string required
  - The custom domain to get information for.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).

### `domain list`

[](#r2-bucket-domain-list)

List [custom domains](/r2/buckets/public-buckets/#custom-domains) for an R2 bucket.

```
wrangler r2 bucket domain list <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket whose connected custom domains will be listed.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).

### `lifecycle add`

[](#r2-bucket-lifecycle-add)

Add an [object lifecycle](/r2/buckets/object-lifecycles/) rule to an R2 bucket.

```
wrangler r2 bucket lifecycle add <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to add a lifecycle rule to.
- `--name` string optional
  - A unique name for the lifecycle rule, used to identify and manage it. For example: `delete-logs-180-days`.
- `--prefix` string optional
  - Prefix condition for the lifecycle rule (leave empty for all prefixes).
- `--expire-days` number optional
  - Sets the lifecycle rule action to expire objects after this number of days. Note you can provide only one of `--expire-days` or `--expire-date`.
- `--expire-date` string optional
  - Sets the lifecycle rule action to expire objects after this date (YYYY-MM-DD). Note you can provide only one of `--expire-days` or `--expire-date`.
- `--ia-transition-days` number optional
  - Sets the lifecycle rule action to transition objects to Infrequent Access storage after this number of days. Note you can provide only one of `--ia-transition-days` or `--ia-transition-date`.
- `--ia-transition-date` string optional
  - Sets the lifecycle rule action to transition objects to Infrequent Access storage after this date (YYYY-MM-DD). Note you can provide only one of `--ia-transition-days` or `--ia-transition-date`.
- `--abort-multipart-days` number optional
  - Sets the lifecycle rule action to abort incomplete multipart uploads after this number of days.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- `--force` boolean optional
  - Skip confirmation when adding the lifecycle rule.

### `lifecycle remove`

[](#r2-bucket-lifecycle-remove)

Remove an [object lifecycle](/r2/buckets/object-lifecycles/) rule from an R2 bucket.

```
wrangler r2 bucket lifecycle remove <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to remove a lifecycle rule from.
- `--name` string required
  - The unique name of the lifecycle rule to remove.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).

### `lifecycle list`

[](#r2-bucket-lifecycle-list)

List [object lifecycle](/r2/buckets/object-lifecycles/) rules for an R2 bucket.

```
wrangler r2 bucket lifecycle list <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to list lifecycle rules for.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).

### `lifecycle set`

[](#r2-bucket-lifecycle-set)

Set the [object lifecycle](/r2/buckets/object-lifecycles/) configuration for an R2 bucket from a JSON file.

```
wrangler r2 bucket lifecycle set <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to set lifecycle configuration for.
- `--file` string required
  - Path to the JSON file containing lifecycle configuration (file must be in format of request body of [put object lifecycle configuration API](/api/resources/r2/subresources/buckets/subresources/lifecycle/methods/update/)).
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- `--force` boolean optional
  - Skip confirmation when setting object lifecycle configuration.

### `lock add`

[](#r2-bucket-lock-add)

Add a [bucket lock](/r2/buckets/bucket-locks/) rule to an R2 bucket.

```
wrangler r2 bucket lock add <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to add a bucket lock rule to.
- `--name` string optional
  - A unique name for the bucket lock rule, used to identify and manage it. For example: `retain-logs-180-days`.
- `--prefix` string optional
  - Prefix condition for the bucket lock rule (leave empty for all prefixes).
- `--retention-days` number optional
  - Sets the number of days to retain objects for. Note you can provide only one of `--retention-days`, `--retention-date`, or `--retention-indefinite`.
- `--retention-date` string optional
  - Sets the number of days to retain objects for. Note you can provide only one of `--retention-days`, `--retention-date`, or `--retention-indefinite`.
- `--retention-indefinite` string optional
  - Sets the retention period to indefinite — meaning the lock will remain in place until explicitly removed. Note you can provide only one of `--retention-days`, `--retention-date`, or `--retention-indefinite`.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- `--force` boolean optional
  - Skip confirmation when adding the bucket lock rule.

### `lock remove`

[](#r2-bucket-lock-remove)

Remove a [bucket lock](/r2/buckets/bucket-locks/) rule from an R2 bucket.

```
wrangler r2 bucket lock remove <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to remove a bucket lock rule from.
- `--name` string required
  - The unique name of the bucket lock rule to remove.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).

### `lock list`

[](#r2-bucket-lock-list)

List [bucket lock](/r2/buckets/bucket-locks/) rules for an R2 bucket.

```
wrangler r2 bucket lock list <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to list bucket locks rules for.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).

### `lock set`

[](#r2-bucket-lock-set)

Set the [bucket lock](/r2/buckets/bucket-locks/) configuration for an R2 bucket from a JSON file.

```
wrangler r2 bucket lock set <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to set bucket lock configuration for.
- `--file` string required
  - Path to the JSON file containing bucket lock configuration (file must be in format of request body of [put bucket lock configuration API](/api/resources/r2/subresources/buckets/subresources/locks/methods/update/)).
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- `--force` boolean optional
  - Skip confirmation when setting bucket lock configuration.

### `notification create`

[](#r2-bucket-notification-create)

Create an [event notification](/r2/buckets/event-notifications/) rule for an R2 bucket.

```
wrangler r2 bucket notification create <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to create an event notification rule for.
- `--event-type` ' object-create ' | ' object-delete ' \[\] required
  - The [type of event(s)](/r2/buckets/event-notifications/#event-types) that will trigger event notifications.
- `--queue` string required
  - The name of the queue that will receive event notification messages.
- `--prefix` string optional
  - The prefix that an object must match to emit event notifications (note: regular expressions are not supported).
- `--suffix` string optional
  - The suffix that an object must match to emit event notifications (note: regular expressions are not supported).
- `--description` string optional
  - A description that can be used to identify the event notification rule after creation.

### `notification delete`

[](#r2-bucket-notification-delete)

Remove an event notification rule from a bucket's [event notification](/r2/buckets/event-notifications/) configuration.

```
wrangler r2 bucket notification delete <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to delete an event notification rule for.
- `--queue` string required
  - The name of the queue that corresponds to the event notification rule. If no `rule` is provided, all event notification rules associated with the queue will be deleted.
- `--rule` string optional
  - The ID of the event notification rule to delete.

### `notification list`

[](#r2-bucket-notification-list)

List the [event notification](/r2/buckets/event-notifications/) rules for a bucket.

```
wrangler r2 bucket notification list <NAME>
```

- `NAME` string required
  - The name of the R2 bucket to get event notification rules for.

### `sippy enable`

[](#r2-bucket-sippy-enable)

Enable [Sippy](/r2/data-migration/sippy/) incremental migration for a bucket.

```
wrangler r2 bucket sippy enable <NAME> [OPTIONS]
```

- `NAME` string required
  - The name of the R2 bucket to enable Sippy.
- `--provider` ' AWS ' | ' GCS ' required
  - The provider of your source object storage bucket.
- `--bucket` string required
  - The name of your source object storage bucket.
- `--r2-key-id` string required
  - Your R2 Access Key ID. Requires read and write access.
- `--r2-secret-access-key` string required
  - Your R2 Secret Access Key. Requires read and write access.
- `--jurisdiction` string optional
  - The jurisdiction where the bucket exists, if a jurisdiction has been specified. Refer to [jurisdictional restrictions](/r2/reference/data-location/#jurisdictional-restrictions).
- **AWS S3 provider-specific options:**
- `--key-id` string optional
  - Your AWS Access Key ID. Requires [read and list access](/r2/data-migration/sippy/#amazon-s3).
- `--secret-access-key` string optional
  - Your AWS Secret Access Key. Requires [read and list access](/r2/data-migration/sippy/#amazon-s3).
- `--region` string optional
  - The AWS region where your S3 bucket is located. For example: `us-west-2`.
- **Google Cloud Storage provider-specific options:**
- `--service-account-key-file` string optional
  - The path to your Google Cloud service account key JSON file. This will read the service account key file and populate `client_email` and `private_key` options. Requires [read and list access](/r2/data-migration/sippy/#google-cloud-storage).
- `--client-email` string optional
  - The client email for your Google Cloud service account key. Requires [read and list access](/r2/data-migration/sippy/#google-cloud-storage).
- `--private-key` string optional
  - The private key for your Google Cloud service account key. Requires [read and list access](/r2/data-migration/sippy/#google-cloud-storage).
- Note that you must provide either `service-account-key-file` or `client_email` and `private_key` for this command to run successfully.

### `sippy disable`

[](#r2-bucket-sippy-disable)

Disable [Sippy](/r2/data-migration/sippy/) incremental migration for a bucket.

```
wrangler r2 bucket sippy disable <NAME>
```

- `NAME` string required
  - The name of the R2 bucket to disable Sippy.

### `sippy get`

[](#r2-bucket-sippy-get)

Get the status of [Sippy](/r2/data-migration/sippy/) incremental migration for a bucket.

```
wrangler r2 bucket sippy get <NAME>
```

- `NAME` string required
  - The name of the R2 bucket to get the status of Sippy.

## `r2 object`

[](#r2-object)

Interact with R2 objects.

### `get`

[](#r2-object-get)

Fetch an object from an R2 bucket.

```
wrangler r2 object get <OBJECT_PATH> [OPTIONS]
```

- `OBJECT_PATH` string required
  - The source object path in the form of `{bucket}/{key}`.
- `--local` boolean (default: true) optional
  - Interact with locally persisted data.
- `--remote` boolean (default: false) optional
  - Interact with remote storage.
- `--persist-to` string optional
  - Specify directory for locally persisted data.

### `put`

[](#r2-object-put)

Create an object in an R2 bucket.

```
wrangler r2 object put <OBJECT_PATH> [OPTIONS]
```

- `OBJECT_PATH` string required
  - The destination object path in the form of `{bucket}/{key}`.
- `--file` string optional
  - The path of the file to upload. Note you must provide either `--file` or `--pipe`.
- `--pipe` boolean optional
  - Enables the file to be piped in, rather than specified with the `--file` option. Note you must provide either `--file` or `--pipe`.
- `--content-type` string optional
  - A standard MIME type describing the format of the object data.
- `--content-disposition` string optional
  - Specifies presentational information for the object.
- `--content-encoding` string optional
  - Specifies what content encodings have been applied to the object and thus what decoding mechanisms must be applied to obtain the media-type referenced by the `Content-Type` header field.
- `--content-language` string optional
  - The language the content is in.
- `--cache-control` string optional
  - Specifies caching behavior along the request/reply chain.
- `--expires` string optional
  - The date and time at which the object is no longer cacheable.
- `--local` boolean (default: true) optional
  - Interact with locally persisted data.
- `--remote` boolean (default: false) optional
  - Interact with remote storage.
- `--persist-to` string optional
  - Specify directory for locally persisted data.

### `delete`

[](#r2-object-delete)

Delete an object in an R2 bucket.

```
wrangler r2 object delete <OBJECT_PATH> [OPTIONS]
```

- `OBJECT_PATH` string required
  - The destination object path in the form of `{bucket}/{key}`.
- `--local` boolean (default: true) optional
  - Interact with locally persisted data.
- `--remote` boolean (default: false) optional
  - Interact with remote storage.
- `--persist-to` string optional
  - Specify directory for locally persisted data.

---

## `secret`

[](#secret)

Manage the secret variables for a Worker.

This action creates a new [version](/workers/configuration/versions-and-deployments/#versions) of the Worker and [deploys](/workers/configuration/versions-and-deployments/#deployments) it immediately. To only create a new version of the Worker, use the [`wrangler versions secret`](/workers/wrangler/commands/#secret-put) commands.

### `put`

[](#put)

Create or replace a secret for a Worker.

```
wrangler secret put <KEY> [OPTIONS]
```

- `KEY` string required
  - The variable name for this secret to be accessed in the Worker.
- `--name` string optional
  - Perform on a specific Worker rather than inheriting from a [Wrangler configuration file](/workers/wrangler/configuration/).
- `--env` string optional
  - Perform on a specific environment.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

When running this command, you will be prompted to input the secret's value:

Terminal window ```
npx wrangler secret put FOO
```

```
? Enter a secret value: › ***🌀 Creating the secret for script worker-app✨ Success! Uploaded secret FOO
```

The `put` command can also receive piped input. For example:

Terminal window ```
echo "-----BEGIN PRIVATE KEY-----\nM...==\n-----END PRIVATE KEY-----\n" | wrangler secret put PRIVATE_KEY
```

### `delete`

[](#delete-1)

Delete a secret for a Worker.

```
wrangler secret delete <KEY> [OPTIONS]
```

- `KEY` string required
  - The variable name for this secret to be accessed in the Worker.
- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).
- `--env` string optional
  - Perform on a specific environment.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `list`

[](#list)

List the names of all the secrets for a Worker.

```
wrangler secret list [OPTIONS]
```

- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).
- `--env` string optional
  - Perform on a specific environment

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

The following is an example of listing the secrets for the current Worker.

Terminal window ```
npx wrangler secret list
```

```
[  {    "name": "FOO",    "type": "secret_text"  }]
```

---

## `secret bulk`

[](#secret-bulk)

Upload multiple secrets for a Worker at once.

```
wrangler secret bulk [<FILENAME>] [OPTIONS]
```

- `FILENAME` string optional
  - A file containing either [JSON ↗](https://www.json.org/json-en.html) or the [.env ↗](https://www.dotenv.org/docs/security/env) format
  - The JSON file containing key-value pairs to upload as secrets, in the form `{"SECRET_NAME": "secret value", ...}`.
  - The `.env` file containing [key-value pairs to upload as secrets](/workers/configuration/secrets/#local-development-with-secrets), in the form `SECRET_NAME=secret value`.
  - If omitted, Wrangler expects to receive input from `stdin` rather than a file.
- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).
- `--env` string optional
  - Perform on a specific environment.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

The following is an example of uploading secrets from a JSON file redirected to `stdin`. When complete, the output summary will show the number of secrets uploaded and the number of secrets that failed to upload.

```
{  "secret-name-1": "secret-value-1",  "secret-name-2": "secret-value-2"}
```

Terminal window ```
npx wrangler secret bulk < secrets.json
```

```
🌀 Creating the secrets for the Worker "script-name"✨ Successfully created secret for key: secret-name-1...🚨 Error uploading secret for key: secret-name-1✨ Successfully created secret for key: secret-name-2
Finished processing secrets JSON file:✨ 1 secrets successfully uploaded🚨 1 secrets failed to upload
```

## `secrets-store secret`

[](#secrets-store-secret)

With the release of [Secrets Store](/secrets-store/) in open beta, you can use the following commands to manage your account secrets.

### `create`

[](#create)

Create a secret within a store.

```
wrangler secrets-store secret create <STORE_ID> [OPTIONS]
```

- `STORE_ID` string required
  - The secret store public ID. You can find it and copy from the [Secrets Store tab ↗](https://dash.cloudflare.com/?to=/:account/secrets-store/) on the dashboard.
- `--name` string required
  - A descriptive name for the account-level secret. Cannot contain spaces.
- `--value` string test only
  - Value of the secret.
- `--scopes` string required
  - Which services will have access to the account-level secret. Currently, only `workers` is available.
- `--comment` string optional
  - Additional information about the account-level secret.
- `--remote` boolean (default: false) optional
  - Execute the command against the remote Secrets Store. To interact with account-level secrets in production, make sure to append `--remote` to your commands.

The following is an example of using the `create` command to create an account-level secret.

Terminal window ```
npx wrangler secrets-store secret create 8f7a1cdced6342c18d223ece462fd88d --name ServiceA_key-1 --scopes workers --remote
```

```
✓ Enter a secret value: › ***
🔐 Creating secret... (Name: ServiceA_key-1, Value: REDACTED, Scopes: workers, Comment: undefined)✓ Select an account: › My account✅ Created secret! (ID: 13bc7498c6374a4e9d13be091c3c65f1)
```

### `update`

[](#update)

Update a secret within a store.

```
wrangler secrets-store secret update <STORE_ID> [OPTIONS]
```

- `STORE_ID` string required
  - The ID of the secrets store that contains the secret you are updating.
- `--secret-id` string required
  - The ID of the secret to update.
- `--value` string test only
  - Updated value of the secret.
- `--scopes` string required
  - Which services will have access to the account-level secret. Currently, only `workers` is available.
- `--comment` string optional
  - Updated comment for the account-level secret.
- `--remote` boolean (default: false) optional
  - Execute the command against the remote Secrets Store. To interact with account-level secrets in production, make sure to append `--remote` to your commands.

### `duplicate`

[](#duplicate)

Duplicate a secret within a store. Use this command to create a new secret that holds the same secret value as an existing secret.

```
wrangler secrets-store secret duplicate <STORE_ID> [OPTIONS]
```

- `STORE_ID` string required
  - The ID of the secrets store that contains the secret you are duplicating.
- `--secret-id` string required
  - The ID of the secret you are duplicating.
- `--name` string required
  - A name for the new secret. Cannot contain spaces.
- `--scopes` string required
  - Which services will have access to the new account-level secret. Currently, only `workers` is available.
- `--comment` string optional
  - Additional information about the new account-level secret.
- `--remote` boolean (default: false) optional
  - Execute the command against the remote Secrets Store. To interact with account-level secrets in production, make sure to append `--remote` to your commands.

### `get`

[](#get)

Get information on a secret within a store.

```
wrangler secrets-store secret get <STORE_ID> [OPTIONS]
```

- `STORE_ID` string required
  - The ID of the secrets store that contains the secret you want to get.
- `--secret-id` string required
  - The ID of the secret you want to get.
- `--remote` boolean (default: false) optional
  - Execute the command against the remote Secrets Store. To interact with account-level secrets in production, make sure to append `--remote` to your commands.

The following is an example with the expected output:

Terminal window ```
npx wrangler secrets-store secret get 8f7a1cdced6342c18d223ece462fd88d --secret-id 13bc7498c6374a4e9d13be091c3c65f1 --remote
```

```
🔐 Getting secret... (ID: 13bc7498c6374a4e9d13be091c3c65f1)✓ Select an account: › My account| Name                        | ID                                  | StoreID                             | Comment | Scopes  | Status  | Created                | Modified               ||-----------------------------|-------------------------------------|-------------------------------------|---------|---------|---------|------------------------|------------------------|| ServiceA_key-1          | 13bc7498c6374a4e9d13be091c3c65f1    | 8f7a1cdced6342c18d223ece462fd88d    |         | workers | active  | 4/9/2025, 10:06:01 PM  | 4/15/2025, 09:13:05 AM |
```

### `delete`

[](#delete-2)

Delete a secret within a store.

```
wrangler secrets-store secret delete <STORE_ID> [OPTIONS]
```

- `STORE_ID` string required
  - The ID of the secrets store that contains the secret you are deleting.
- `--secret-id` string required
  - The ID of the secret you are deleting.
- `--remote` boolean (default: false) optional
  - Execute the command against the remote Secrets Store. To interact with account-level secrets in production, make sure to append `--remote` to your commands.

### `list`

[](#list-1)

List secrets within a store.

```
wrangler secrets-store secret list <STORE_ID>
```

- `STORE_ID` string required
  - The secret store public ID. You can find it and copy from the [Secrets Store tab ↗](https://dash.cloudflare.com/?to=/:account/secrets-store/) on the dashboard.

## `secrets-store store`

[](#secrets-store-store)

Use the following commands to manage your store.

### `create`

[](#create-1)

Create a store within Secrets Store.

```
wrangler secrets-store store create <name>
```

- `name` string required
  - A descriptive name for the account-level secret. Cannot contain spaces.
- `--remote` boolean (default: false) required
  - Execute the command against the remote Secrets Store.

The following is an example of using the `create` command to create a store.

Terminal window ```
npx wrangler secrets-store store create default --remote
```

```
🔐 Creating store... (Name: default)✅ Created store! (Name: default, ID: 2e2a82d317134506b58defbe16982d54)
```

### `delete`

[](#delete-3)

Delete a store within Secrets Store.

```
wrangler secrets-store store delete <STORE_ID>
```

- `STORE_ID` string required
  - The secret store public ID. You can find it and copy from the [Secrets Store tab ↗](https://dash.cloudflare.com/?to=/:account/secrets-store/) on the dashboard.
- `--remote` boolean (default: false) required
  - Execute the command against the remote Secrets Store.

The following is an example of using the `delete` command to delete a store.

Terminal window ```
npx wrangler secrets-store store delete d2dafaeac9434de2b6d08b292ce08211 --remote
```

```
🔐 Deleting store... (Name: d2dafaeac9434de2b6d08b292ce08211)✅ Deleted store! (ID: d2dafaeac9434de2b6d08b292ce08211)
```

### `list`

[](#list-2)

List the stores within an account.

```
wrangler secrets-store store list
```

- `--remote` boolean (default: false) required
  - Execute the command against the remote Secrets Store.

The following is an example of using the `list` command to list stores.

Terminal window ```
npx wrangler secrets-store store list --remote
```

```
🔐 Listing stores...┌─────────┬──────────────────────────────────┬──────────────────────────────────┬──────────────────────┬──────────────────────┐│ Name    │ ID                               │ AccountID                        │ Created              │ Modified             │├─────────┼──────────────────────────────────┼──────────────────────────────────┼──────────────────────┼──────────────────────┤│ default │ 8876bad33f164462bf0743fe8adf98f4 │ REDACTED │ 4/9/2025, 1:11:48 PM  │ 4/9/2025, 1:11:48 PM │└─────────┴──────────────────────────────────┴──────────────────────────────────┴──────────────────────┴──────────────────────┘
```

## `workflows`

[](#workflows)

Manage and configure [Workflows](/workflows/).

### `list`

[](#list-3)

Lists the registered Workflows for this account.

Terminal window ```
wrangler workflows list
```

- `--page` number optional
  - Show a specific page from the listing. You can configure page size using "per-page".
- `--per-page` number optional
  - Configure the maximum number of Workflows to show per page.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `instances`

[](#instances)

Manage and interact with specific instances of a Workflow.

### `instances list`

[](#instances-list)

List Workflow instances.

Terminal window ```
wrangler workflows instances list <WORKFLOW_NAME> [OPTIONS]
```

- `WORKFLOW_NAME` string required
  - The name of a registered Workflow.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `instances describe`

[](#instances-describe)

Describe a specific instance of a Workflow, including its current status, any persisted state, and per-step outputs.

Terminal window ```
wrangler workflows instances describe <WORKFLOW_NAME> [ID] [OPTIONS]
```

- `WORKFLOW_NAME` string required
  - The name of a registered Workflow.
- `ID` string (default: latest) optional
  - The ID of a Workflow instance. You can optionally provide `latest` to refer to the most recently created instance of a Workflow. Defaults to `latest` if no ID is provided.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

Terminal window ```
# Passing `latest` instead of an explicit ID will describe the most recently queued instancewrangler workflows instances describe my-workflow latest
```

```
Workflow Name:         my-workflowInstance Id:           51c73fc8-7fd5-47d9-bd82-9e301506ee72Version Id:            cedc33a0-11fa-4c26-8a8e-7d28d381a291Status:                ✅ CompletedTrigger:               🌎 APIQueued:                10/16/2024, 2:00:39 PMSuccess:               ✅ YesStart:                 10/16/2024, 2:00:39 PMEnd:                   10/16/2024, 2:01:40 PMDuration:              1 minute# Remaining output truncated
```

### `instances terminate`

[](#instances-terminate)

Terminate (permanently stop) a Workflow instance.

Terminal window ```
wrangler workflows instances terminate <WORKFLOW_NAME> <ID> [OPTIONS]
```

- `WORKFLOW_NAME` string required
  - The name of a registered Workflow.
- `ID` string required
  - The ID of a Workflow instance.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `instances pause`

[](#instances-pause)

Pause (until resumed) a Workflow instance.

Terminal window ```
wrangler workflows instances pause <WORKFLOW_NAME> <ID> [OPTIONS]
```

- `WORKFLOW_NAME` string required
  - The name of a registered Workflow.
- `ID` string required
  - The ID of a Workflow instance.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `instances resume`

[](#instances-resume)

Resume a paused Workflow instance.

Terminal window ```
wrangler workflows instances resume <WORKFLOW_NAME> <ID> [OPTIONS]
```

- `WORKFLOW_NAME` string required
  - The name of a registered Workflow.
- `ID` string required
  - The ID of a Workflow instance.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `describe`

[](#describe)

Terminal window ```
wrangler workflows describe <WORKFLOW_NAME> [OPTIONS]
```

- `WORKFLOW_NAME` string required
  - The name of a registered Workflow.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `delete`

[](#delete-4)

Delete a Workflow and all its instances.

Terminal window ```
wrangler workflows delete <WORKFLOW_NAME> [OPTIONS]
```

- `WORKFLOW_NAME` string required
  - The name of a registered Workflow.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

Terminal window ```
wrangler workflows instances delete my-workflow
```

### `trigger`

[](#trigger)

Trigger (create) a Workflow instance.

Terminal window ```
wrangler workflows trigger <WORKFLOW_NAME> <PARAMS> [OPTIONS]
```

- `WORKFLOW_NAME` string required
  - The name of a registered Workflow.
- `PARAMS` string optional
  - The parameters to pass to the Workflow as an event. Must be a JSON-encoded string.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

Terminal window ```
# Pass optional params to the Workflow.wrangler workflows trigger my-workflow '{"hello":"world"}'
```

## `tail`

[](#tail)

Start a session to livestream logs from a deployed Worker.

```
wrangler tail <WORKER> [OPTIONS]
```

- `WORKER` string required
  - The name of your Worker or the route the Worker is running on.
- `--format` ' json ' | ' pretty ' optional
  - The format of the log entries.
- `--status` ' ok ' | ' error ' | ' canceled ' optional
  - Filter by invocation status.
- `--header` string optional
  - Filter by HTTP header.
- `--method` string optional
  - Filter by HTTP method.
- `--sampling-rate` number optional
  - Add a fraction of requests to log sampling rate (between `0` and `1`).
- `--search` string optional
  - Filter by a text match in `console.log` messages.
- `--ip` (string| ' self ')\\\[\] " optional
  - Filter by the IP address the request originates from. Use `"self"` to show only messages from your own IP.
- `--version-id` string optional
  - Filter by Worker version.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

After starting `wrangler tail`, you will receive a live feed of console and exception logs for each request your Worker receives.

If your Worker has a high volume of traffic, the tail might enter sampling mode. This will cause some of your messages to be dropped and a warning to appear in your tail logs. To prevent messages from being dropped, add the options listed above to filter the volume of tail messages.

If sampling persists after using options to filter messages, consider using [instant logs ↗](https://developers.cloudflare.com/logs/instant-logs/).

---

## `pages`

[](#pages)

Configure Cloudflare Pages.

### `dev`

[](#dev-1)

Develop your full-stack Pages application locally.

```
wrangler pages dev [<DIRECTORY>] [OPTIONS]
```

- `DIRECTORY` string optional
  - The directory of static assets to serve.
- `--local` boolean optional (default: true)
  - Run on your local machine.
- `--ip` string optional
  - IP address to listen on, defaults to `localhost`.
- `--port` number optional (default: 8788)
  - The port to listen on (serve from).
- `--config`, `-c` string\[\] optional
  - Path(s) to [Wrangler configuration file](/workers/wrangler/configuration/). If not provided, Wrangler will use the nearest config file based on your current working directory.
  - You can provide additional configuration files in order to run Workers alongside your Pages project, like this: `wrangler pages dev -c ./wrangler.toml -c ../other-worker/wrangler.toml`. The first argument must point to your Pages configuration file, and the subsequent configurations will be accessible via a Service binding from your Pages project.
- `--binding` string\[\] optional
  - Bind an environment variable or secret (for example, `--binding < VARIABLE_NAME>= < VALUE>`).
- `--kv` string\[\] optional
  - Binding name of [KV namespace](/kv/) to bind (for example, `--kv < BINDING_NAME>`).
- `--r2` string\[\] optional
  - Binding name of [R2 bucket](/pages/functions/bindings/#interact-with-your-r2-buckets-locally) to bind (for example, `--r2 < BINDING_NAME>`).
- `--d1` string\[\] optional
  - Binding name of [D1 database](/pages/functions/bindings/#interact-with-your-d1-databases-locally) to bind (for example, `--d1 < BINDING_NAME>`).
- `--do` string\[\] optional
  - Binding name of Durable Object to bind (for example, `--do < BINDING_NAME>= < CLASS>`).
- `--live-reload` boolean optional (default: false)
  - Auto reload HTML pages when change is detected.
- `--compatibility-flag` string\[\] optional
  - Runtime compatibility flags to apply.
- `--compatibility-date` string optional
  - Runtime compatibility date to apply.
- `--show-interactive-dev-session` boolean optional (default: true if the terminal supports interactivity)
  - Show the interactive dev session.
- `--https-key-path` string optional
  - Path to a custom certificate key.
- `--https-cert-path` string optional
  - Path to a custom certificate.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

[](#download-config)

Download your Pages project config as a [Wrangler configuration file](/workers/wrangler/configuration/).

```
wrangler pages download config <PROJECT_NAME>
```

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `project list`

[](#project-list)

List your Pages projects.

```
wrangler pages project list
```

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `project create`

[](#project-create)

Create a new Cloudflare Pages project.

```
wrangler pages project create <PROJECT_NAME> [OPTIONS]
```

- `PROJECT_NAME` string required
  - The name of your Pages project.
- `--production-branch` string optional
  - The name of the production branch of your project.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `project delete`

[](#project-delete)

Delete a Cloudflare Pages project.

```
wrangler pages project delete <PROJECT_NAME> [OPTIONS]
```

- `PROJECT_NAME` string required
  - The name of the Pages project to delete.
- `--yes` boolean optional
  - Answer `"yes"` to confirmation prompt.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `deployment list`

[](#deployment-list)

List deployments in your Cloudflare Pages project.

```
wrangler pages deployment list [--project-name <PROJECT_NAME>]
```

- `--project-name` string optional
  - The name of the project you would like to list deployments for.
- `--environment` ' production ' | ' preview ' optional
  - Environment type to list deployments for.
- `--json` boolean optional
  - Whether to output the list in JSON format.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `deployment tail`

[](#deployment-tail)

Start a session to livestream logs from your deployed Pages Functions.

```
wrangler pages deployment tail [<DEPLOYMENT>] [OPTIONS]
```

- `DEPLOYMENT` string optional
  - ID or URL of the deployment to tail. Specify by environment if deployment ID is unknown.
- `--project-name` string optional
  - The name of the project you would like to tail.
- `--environment` ' production ' | ' preview ' optional
  - When not providing a specific deployment ID, specifying environment will grab the latest production or preview deployment.
- `--format` ' json ' | ' pretty ' optional
  - The format of the log entries.
- `--status` ' ok ' | ' error ' | ' canceled ' optional
  - Filter by invocation status.
- `--header` string optional
  - Filter by HTTP header.
- `--method` string optional
  - Filter by HTTP method.
- `--sampling-rate` number optional
  - Add a percentage of requests to log sampling rate.
- `--search` string optional
  - Filter by a text match in `console.log` messages.
- `--ip` (string| ' self ')\\\[\] optional
  - Filter by the IP address the request originates from. Use `"self"` to show only messages from your own IP.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

After starting `wrangler pages deployment tail`, you will receive a live stream of console and exception logs for each request your Functions receive.

### `deploy`

[](#deploy-1)

Deploy a directory of static assets as a Pages deployment.

```
wrangler pages deploy <BUILD_OUTPUT_DIRECTORY> [OPTIONS]
```

- `BUILD_OUTPUT_DIRECTORY` string optional
  - The [directory](/pages/configuration/build-configuration/#framework-presets) of static files to upload. As of Wrangler 3.45.0, this is only required when your Pages project does not have a Wrangler file. Refer to the [Pages Functions configuration guide](/pages/functions/wrangler-configuration/) for more information.
- `--project-name` string optional
  - The name of the project you want to deploy to.
- `--branch` string optional
  - The name of the branch you want to deploy to.
- `--commit-hash` string optional
  - The SHA to attach to this deployment.
- `--commit-message` string optional
  - The commit message to attach to this deployment.
- `--commit-dirty` boolean optional
  - Whether or not the workspace should be considered dirty for this deployment.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `secret put`

[](#secret-put)

Create or update a secret for a Pages project.

```
wrangler pages secret put <KEY> [OPTIONS]
```

- `KEY` string required
  - The variable name for this secret to be accessed in the Pages project.
- `--project-name` string optional
  - The name of your Pages project.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `secret delete`

[](#secret-delete)

Delete a secret from a Pages project.

```
wrangler pages secret delete <KEY> [OPTIONS]
```

- `KEY` string required
  - The variable name for this secret to be accessed in the Pages project.
- `--project-name` string optional
  - The name of your Pages project.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `secret list`

[](#secret-list)

List the names of all the secrets for a Pages project.

```
wrangler pages secret list [OPTIONS]
```

- `--project-name` string optional
  - The name of your Pages project.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `secret bulk`

[](#secret-bulk-1)

Upload multiple secrets for a Pages project at once.

```
wrangler pages secret bulk [<FILENAME>] [OPTIONS]
```

- `FILENAME` string optional
  - A file containing either [JSON ↗](https://www.json.org/json-en.html) or the [.env ↗](https://www.dotenv.org/docs/security/env) format
  - The JSON file containing key-value pairs to upload as secrets, in the form `{"SECRET_NAME": "secret value", ...}`.
  - The `.env` file containing [key-value pairs to upload as secrets](/workers/configuration/secrets/#local-development-with-secrets), in the form `SECRET_NAME=secret value`.
  - If omitted, Wrangler expects to receive input from `stdin` rather than a file.
- `--project-name` string optional
  - The name of your Pages project.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `functions build`

[](#functions-build)

Compile a folder of Pages Functions into a single Worker.

```
wrangler pages functions build [<DIRECTORY>] [OPTIONS]
```

- `DIRECTORY` string optional (default: \`functions\`)
  - The directory of Pages Functions.
- `--outdir` string optional
  - Output directory for the bundled Worker.
- `--fallback-service` string optional (default: \`ASSETS\`)
  - The service to fallback to at the end of the `next` chain. Setting to `''` will fallback to the global `fetch`.
- `--compatibility-date` string optional
  - Date to use for compatibility checks.
- `--compatibility-flags` string\[\] optional
  - Flags to use for compatibility checks.
- `--metafile` string optional
  - Specify a file to write the build metadata from esbuild to. If flag is used without a path string, this defaults to `bundle-meta.json` inside the directory specified by `--outdir`. This can be useful for understanding the bundle size.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## `pipelines`

[](#pipelines)

Manage your [Pipelines](/pipelines/).

### `create`

[](#pipelines-create)

Create a new pipeline

```
wrangler pipelines create <name> --r2 <r2-bucket-name> [OPTIONS]
```

- `name` string required
  - The name of the pipeline to create
- `--source` array optional
  - List of allowed sources. Options: `http` or `worker`
- `--require-http-auth` boolean optional
  - Require Cloudflare API token to authenticate with the HTTPS endpoint. Defaults to `false`.
- `--cors-origins` array optional
  - CORS Origin allowlist for HTTP endpoint. Allows `*`. Defaults to an empty array.
- `--batch-max-mb` number optional
  - The maximum size of a batch in megabytes before data is written. Defaults to `100`. Must be between `1` and `100`.
- `--batch-max-rows` number optional
  - The maximum number of rows in a batch before data is written. Defaults to `10000000`. Must be between `1` and `10000000`.
- `--batch-max-seconds` number optional
  - The maximum duration of a batch before data is written in seconds. Defaults to `300`. Must be between `1` and `300`.
- `--r2-bucket` string required
  - The name of the R2 bucket used as the destination to store the data.
- `--r2-bucket-access-key-id` string optional
  - Access key ID used to authenticate with R2. Leave empty for oauth confirmation.
- `--r2-bucket-secret-access-key` string optional
  - Secret access key ID used to authenticate with R2. Leave empty for oauth confirmation.
- `--r2-prefix` string optional
  - Prefix for storing files in the destination bucket.
- `--compression` string optional
  - Type of compression to apply to output files. Choices: `none`, `gzip`, `deflate`
- `--shard-count` number optional
  - Number of pipeline shards. More shards handle higher request volume; fewer shards produce larger output files. Defaults to `2`. Must be between `1` and `15`.

### `update`

[](#pipelines-update)

Update an existing pipeline

```
wrangler pipelines update <name> [OPTIONS]
```

- `name` string required
  - The name of the pipeline to create
- `--source` array optional
  - List of allowed sources. Options: `http` or `worker`
- `--require-http-auth` boolean optional
  - Require Cloudflare API token to authenticate with the HTTPS endpoint. Defaults to `false`.
- `--cors-origins` array optional
  - CORS Origin allowlist for HTTP endpoint. Allows `*`. Defaults to an empty array.
- `--batch-max-mb` number optional
  - The maximum size of a batch in megabytes before data is written. Defaults to `100`. Must be between `1` and `100`.
- `--batch-max-rows` number optional
  - The maximum number of rows in a batch before data is written. Defaults to `10000000`. Must be between `1` and `10000000`.
- `--batch-max-seconds` number optional
  - The maximum duration of a batch before data is written in seconds. Defaults to `300`. Must be between `1` and `300`.
- `--r2-bucket` string required
  - The name of the R2 bucket used as the destination to store the data.
- `--r2-bucket-access-key-id` string optional
  - Access key ID used to authenticate with R2. Leave empty for oauth confirmation.
- `--r2-bucket-secret-access-key` string optional
  - Secret access key ID used to authenticate with R2. Leave empty for oauth confirmation.
- `--r2-prefix` string optional
  - Prefix for storing files in the destination bucket.
- `--compression` string optional
  - Type of compression to apply to output files. Choices: `none`, `gzip`, `deflate`
- `--shard-count` number optional
  - Number of pipeline shards. More shards handle higher request volume; fewer shards produce larger output files. Defaults to `2`. Must be between `1` and `15`.

### `get`

[](#pipelines-get)

Get the configuration for an existing pipeline.

```
wrangler pipelines get <name> [OPTIONS]
```

- `name` string required
  - The name of the pipeline to inspect

### `delete`

[](#pipelines-delete)

Deletes an existing pipeline

```
wrangler pipelines delete <name> [OPTIONS]
```

- `name` string required
  - The name of the pipeline to delete

### `list`

[](#pipelines-list)

Lists all pipelines in your account.

```
wrangler pipelines list [OPTIONS]
```

---

## `queues`

[](#queues)

Manage your Workers [Queues](/queues/) configurations.

### `create`

[](#queues-create)

Create a new queue.

```
wrangler queues create <name> [OPTIONS]
```

- `name` string required
  - The name of the queue to create.
- `--delivery-delay-secs` number optional
  - How long a published message should be delayed for, in seconds. Must be a positive integer.
- `--message-retention-period-secs` number optional
  - How long a published message is retained in the Queue. Must be a positive integer between 60 and 1209600 (14 days). Defaults to 345600 (4 days).

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `update`

[](#queues-update)

Update an existing queue.

```
wrangler queues update <name> [OPTIONS]
```

- `name` string required
  - The name of the queue to update.
- `--delivery-delay-secs` number optional
  - How long a published message should be delayed for, in seconds. Must be a positive integer.
- `--message-retention-period-secs` number optional
  - How long a published message is retained on the Queue. Must be a positive integer between 60 and 1209600 (14 days). Defaults to 345600 (4 days).

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `delete`

[](#queues-delete)

Delete an existing queue.

```
wrangler queues delete <name> [OPTIONS]
```

- `name` string required
  - The name of the queue to delete.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `list`

[](#queues-list)

List all queues in the current account.

```
wrangler queues list [OPTIONS]
```

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `info`

[](#queues-info)

Get information on individual queues.

```
wrangler queues info <name>
```

- `name` string required
  - The name of the queue to inspect.

### `consumer`

[](#queues-consumer)

Manage queue consumer configurations.

### `consumer add < script-name>`

[](#queues-consumer-add-script-name)

Add a Worker script as a [queue consumer](/queues/reference/how-queues-works/#consumers).

```
wrangler queues consumer add <queue-name> <script-name> [OPTIONS]
```

- `queue-name` string required
  - The name of the queue to add the consumer to.
- `script-name` string required
  - The name of the Workers script to add as a consumer of the named queue.
- `--batch-size` number optional
  - Maximum number of messages per batch. Must be a positive integer.
- `--batch-timeout` number optional
  - Maximum number of seconds to wait to fill a batch with messages. Must be a positive integer.
- `--message-retries` number optional
  - Maximum number of retries for each message. Must be a positive integer.
- `--max-concurrency` number optional
  - The maximum number of concurrent consumer invocations that will be scaled up to handle incoming message volume. Must be a positive integer.
- `--retry-delay-secs` number optional
  - How long a retried message should be delayed for, in seconds. Must be a positive integer.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `consumer remove`

[](#queues-consumer-remove)

Remove a consumer from a queue.

```
wrangler queues consumer remove <queue-name> <script-name>
```

- `queue-name` string required
  - The name of the queue to remove the consumer from.
- `script-name` string required
  - The name of the Workers script to remove as the consumer.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `purge`

[](#queues-purge)

Permanently delete all messages in a queue.

```
wrangler queues purge <queue-name>
```

- `queue-name` string required
  - The name of the queue from which messages should be deleted.

### `pause-delivery`

[](#queues-pause-delivery)

Pause message delivery from a Queue to consumers (including push consumers, and HTTP pull consumers)

```
wrangler queues pause-delivery <queue-name>
```

- `queue-name` string required
  - The name of the queue which delivery should be paused.

### `resume-delivery`

[](#queues-resume-delivery)

Resume delivery from a Queue to consumers (including push consumers, and HTTP pull consumers)

```
wrangler queues resume-delivery <queue-name>
```

- `queue-name` string required
  - The name of the queue from which delivery should be resumed.

### `subscription create`

[](#queues-subscription-create)

Create a new [event subscription](/queues/event-subscriptions/) for a queue.

```
wrangler queues subscription create <queue-name> [OPTIONS]
```

- `queue-name` string required
  - The name of the queue to create the subscription for.
- `--source` string required
  - The event source type. Supported sources: `kv`, `r2`, `superSlurper`, `vectorize`, `workersAi.model`, `workersBuilds.worker`, `workflows.workflow`.
- `--events` string required
  - Comma-separated list of event types to subscribe to. Refer to [Events & schemas](/queues/event-subscriptions/events-schemas/) for a complete list of all supported events.
- `--name` string optional
  - Name for the subscription. Auto-generated if not provided.
- `--enabled` boolean optional
  - Whether the subscription should be active. Defaults to true.
- Additional source-specific options (e.g., `--worker-name` for workersBuilds.worker, `--bucket-name` for r2.bucket).

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `subscription list`

[](#queues-subscription-list)

List all [event subscriptions](/queues/event-subscriptions/) for a queue.

```
wrangler queues subscription list <queue-name> [OPTIONS]
```

- `queue-name` string required
  - The name of the queue to list subscriptions for.
- `--page` number optional
  - Show a specific page from the listing. You can configure page size using "per-page".
- `--per-page` number optional
  - Configure the maximum number of subscriptions to show per page.
- `--json` boolean optional
  - Output in JSON format.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `subscription get`

[](#queues-subscription-get)

Get details about a specific [event subscription](/queues/event-subscriptions/).

```
wrangler queues subscription get <queue-name> [OPTIONS]
```

- `queue-name` string required
  - The name of the queue.
- `--id` string required
  - The ID of the subscription to retrieve.
- `--json` boolean optional
  - Output in JSON format.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `subscription update`

[](#queues-subscription-update)

Update an existing [event subscription](/queues/event-subscriptions/).

```
wrangler queues subscription update <queue-name> [OPTIONS]
```

- `queue-name` string required
  - The name of the queue.
- `--id` string required
  - The ID of the subscription to update.
- `--name` string optional
  - New name for the subscription.
- `--events` string optional
  - Comma-separated list of event types to subscribe to.
- `--enabled` boolean optional
  - Whether the subscription should be active.
- `--json` boolean optional
  - Output in JSON format.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `subscription delete`

[](#queues-subscription-delete)

Delete an [event subscription](/queues/event-subscriptions/).

```
wrangler queues subscription delete <queue-name> [OPTIONS]
```

- `queue-name` string required
  - The name of the queue.
- `--id` string required
  - The ID of the subscription to delete.
- `--force` boolean optional
  - Skip confirmation prompt.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## `login`

[](#login)

Authorize Wrangler with your Cloudflare account using OAuth. Wrangler will attempt to automatically open your web browser to login with your Cloudflare account.

If you prefer to use API tokens for authentication, such as in headless or continuous integration environments, refer to [Running Wrangler in CI/CD](/workers/ci-cd/).

```
wrangler login [OPTIONS]
```

- `--scopes-list` string optional
  - List all the available OAuth scopes with descriptions.
- `--scopes` string optional
  - Allows to choose your set of OAuth scopes. The set of scopes must be entered in a whitespace-separated list,
  for example, `npx wrangler login --scopes account:read user:read`.
- `--callback-host` string optional
  - Defaults to `localhost`. Sets the IP or hostname where Wrangler should listen for the OAuth callback.
- `--callback-port` string optional
  - Defaults to `8976`. Sets the port where Wrangler should listen for the OAuth callback.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

If Wrangler fails to open a browser, you can copy and paste the URL generated by `wrangler login` in your terminal into a browser and log in.

### Use `wrangler login` on a remote machine

[](#use-wrangler-login-on-a-remote-machine)

If you are using Wrangler from a remote machine, but run the login flow from your local browser, you will receive the following error message after logging in: `This site can't be reached`.

To finish the login flow, run `wrangler login` and go through the login flow in the browser:

Terminal window ```
npx wrangler login
```

```
 ⛅️ wrangler 2.1.6-------------------Attempting to login via OAuth...Opening a link in your default browser: https://dash.cloudflare.com/oauth2/auth?xyz...
```

The browser login flow will redirect you to a `localhost` URL on your machine.

Leave the login flow active. Open a second terminal session. In that second terminal session, use `curl` or an equivalent request library on the remote machine to fetch this `localhost` URL. Copy and paste the `localhost` URL that was generated during the `wrangler login` flow and run:

Terminal window ```
curl <LOCALHOST_URL>
```

---

## `logout`

[](#logout)

Remove Wrangler's authorization for accessing your account. This command will invalidate your current OAuth token.

```
wrangler logout
```

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

If you are using `CLOUDFLARE_API_TOKEN` instead of OAuth, and you can logout by deleting your API token in the Cloudflare dashboard:

1. Log in to the [Cloudflare dashboard ↗](https://dash.cloudflare.com/).
1. Go to **My Profile** > **API Tokens**.
1. Select the three-dot menu on your Wrangler token.
1. Select **Delete**.

---

## `whoami`

[](#whoami)

Retrieve your user information and test your authentication configuration.

```
wrangler whoami
```

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## `versions`

[](#versions)

### `upload`

[](#upload)

Upload a new [version](/workers/configuration/versions-and-deployments/#versions) of your Worker that is not deployed immediately.

```
wrangler versions upload [OPTIONS]
```

- `--tag` string optional
  - Add a version tag. Accepts empty string.
- `--message` string optional
  - Add a version message. Accepts empty string.
- `--preview-alias` string optional
  - Creates an alias to this version.
- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).
- `--env` string optional
  - Perform on a specific environment.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `deploy`

[](#deploy-2)

Deploy a previously created [version](/workers/configuration/versions-and-deployments/#versions) of your Worker all at once or create a [gradual deployment](/workers/configuration/versions-and-deployments/gradual-deployments/) to incrementally shift traffic to a new version by following an interactive prompt.

```
wrangler versions deploy [OPTIONS]
```

- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `list`

[](#list-4)

Retrieve details for the 10 most recent versions. Details include `Version ID`, `Created on`, `Author`, `Source`, and optionally, `Tag` or `Message`.

```
wrangler versions list [OPTIONS]
```

- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `secret put`

[](#secret-put-1)

Create or replace a secret for a Worker. Creates a new [version](/workers/configuration/versions-and-deployments/#versions) with modified secrets without [deploying](/workers/configuration/versions-and-deployments/#deployments) the Worker.

```
wrangler versions secret put <KEY> [OPTIONS]
```

- `KEY` string required
  - The variable name for this secret to be accessed in the Worker.
- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).
- `--env` string optional
  - Perform on a specific environment.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `secret delete`

[](#secret-delete-1)

Delete a secret for a Worker. Creates a new [version](/workers/configuration/versions-and-deployments/#versions) with modified secrets without [deploying](/workers/configuration/versions-and-deployments/#deployments) the Worker.

```
wrangler versions secret delete <KEY> [OPTIONS]
```

- `KEY` string required
  - The variable name for this secret to be accessed in the Worker.
- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).
- `--env` string optional
  - Perform on a specific environment.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `secret bulk`

[](#secret-bulk-2)

Upload multiple secrets for a Worker at once. Creates a new [version](/workers/configuration/versions-and-deployments/#versions) with modified secrets without [deploying](/workers/configuration/versions-and-deployments/#deployments) the Worker.

```
wrangler versions secret bulk <FILENAME> [OPTIONS]
```

- `FILENAME` string optional
  - A file containing either [JSON ↗](https://www.json.org/json-en.html) or the [.env ↗](https://www.dotenv.org/docs/security/env) format
  - The JSON file containing key-value pairs to upload as secrets, in the form `{"SECRET_NAME": "secret value", ...}`.
  - The `.env` file containing key-value pairs to upload as secrets, in the form `SECRET_NAME=secret value`.
  - If omitted, Wrangler expects to receive input from `stdin` rather than a file.
- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).
- `--env` string optional
  - Perform on a specific environment.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## `triggers`

[](#triggers)

### `deploy`

[](#deploy-3)

Apply changes to triggers ( [Routes or domains](/workers/configuration/routing/) and [Cron Triggers](/workers/configuration/cron-triggers/)) when using [`wrangler versions upload`](/workers/wrangler/commands/#upload).

```
wrangler triggers deploy [OPTIONS]
```

- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## `deployments`

[](#deployments)

[Deployments](/workers/configuration/versions-and-deployments/#deployments) track the version(s) of your Worker that are actively serving traffic.

### `list`

[](#list-5)

Retrieve details for the 10 most recent [deployments](/workers/configuration/versions-and-deployments/#deployments). Details include `Created on`, `Author`, `Source`, an optional `Message`, and metadata about the `Version(s)` in the deployment.

```
wrangler deployments list [OPTIONS]
```

- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `status`

[](#status)

Retrieve details for the most recent deployment. Details include `Created on`, `Author`, `Source`, an optional `Message`, and metadata about the `Version(s)` in the deployment.

```
wrangler deployments status
```

- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

## `rollback`

[](#rollback)

```
wrangler rollback [<VERSION_ID>] [OPTIONS]
```

- `VERSION_ID` string optional
  - The ID of the version you wish to roll back to. If not supplied, the `rollback` command defaults to the version uploaded before the latest version.
- `--name` string optional
  - Perform on a specific Worker rather than inheriting from the [Wrangler configuration file](/workers/wrangler/configuration/).
- `--message` string optional
  - Add message for rollback. Accepts empty string. When specified, interactive prompts for rollback confirmation and message are skipped.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## dispatch namespace

[](#dispatch-namespace)

### `list`

[](#list-6)

List all dispatch namespaces.

```
wrangler dispatch-namespace list
```

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `get`

[](#get-1)

Get information about a dispatch namespace.

```
wrangler dispatch-namespace get <NAME>
```

- `NAME` string required
  - The name of the dispatch namespace to get details about.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `create`

[](#create-2)

Create a dispatch namespace.

```
wrangler dispatch-namespace create <NAME>
```

- `NAME` string required
  - The name of the dispatch namespace to create.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `delete`

[](#delete-5)

Delete a dispatch namespace.

```
wrangler dispatch-namespace get <NAME>
```

- `NAME` string required
  - The name of the dispatch namespace to delete.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

### `rename`

[](#rename)

Rename a dispatch namespace.

```
wrangler dispatch-namespace get <OLD_NAME> <NEW_NAME>
```

- `OLD_NAME` string required
  - The previous name of the dispatch namespace.
- `NEW_NAME` string required
  - The new name of the dispatch namespace.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## `mtls-certificate`

[](#mtls-certificate)

Manage client certificates used for mTLS connections in subrequests.

These certificates can be used in [`mtls_certificate` bindings](/workers/runtime-apis/bindings/mtls), which allow a Worker to present the certificate when establishing a connection with an origin that requires client authentication (mTLS).

[](#upload-1)

Upload a client certificate.

```
wrangler mtls-certificate upload --cert <PATH> --key <PATH> [OPTIONS]
```

- `--cert` string required
  - A path to the TLS certificate to upload. Certificate chains are supported.
- `--key` string required
  - A path to the private key to upload.
- `--name` string optional
  - The name assigned to the mTLS certificate at upload.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

The following is an example of using the `upload` command to upload an mTLS certificate.

Terminal window ```
npx wrangler mtls-certificate upload --cert cert.pem --key key.pem --name my-origin-cert
```

```
Uploading mTLS Certificate my-origin-cert...Success! Uploaded mTLS Certificate my-origin-certID: 99f5fef1-6cc1-46b8-bd79-44a0d5082b8dIssuer: CN=my-secured-origin.com,OU=my-team,O=my-org,L=San Francisco,ST=California,C=USExpires: 1/01/2025
```

You can then add this certificate as a [binding](/workers/runtime-apis/bindings/) in your [Wrangler configuration file](/workers/wrangler/configuration/):

- [wrangler.jsonc](#tab-panel-2780)
- [wrangler.toml](#tab-panel-2781)

```
{  "mtls_certificates": [    {      "binding": "MY_CERT",      "certificate_id": "99f5fef1-6cc1-46b8-bd79-44a0d5082b8d"    }  ]}
```

```
mtls_certificates = [  { binding = "MY_CERT", certificate_id = "99f5fef1-6cc1-46b8-bd79-44a0d5082b8d" }]
```

Note that the certificate and private keys must be in separate (typically `.pem`) files when uploading.

### `list`

[](#list-7)

List mTLS certificates associated with the current account ID.

```
wrangler mtls-certificate list
```

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

The following is an example of using the `list` command to upload an mTLS certificate.

Terminal window ```
npx wrangler mtls-certificate list
```

```
ID: 99f5fef1-6cc1-46b8-bd79-44a0d5082b8dName: my-origin-certIssuer: CN=my-secured-origin.com,OU=my-team,O=my-org,L=San Francisco,ST=California,C=USCreated on: 1/01/2023Expires: 1/01/2025
ID: c5d004d1-8312-402c-b8ed-6194328d5cbeIssuer: CN=another-origin.com,OU=my-team,O=my-org,L=San Francisco,ST=California,C=USCreated on: 1/01/2023Expires: 1/01/2025
```

### `delete`

[](#delete-6)

Delete a client certificate.

```
wrangler mtls-certificate delete {--id <ID|--name <NAME>}
```

- `--id` string
  - The ID of the mTLS certificate.
- `--name` string
  - The name assigned to the mTLS certificate at upload.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

The following is an example of using the `delete` command to delete an mTLS certificate.

Terminal window ```
npx wrangler mtls-certificate delete --id 99f5fef1-6cc1-46b8-bd79-44a0d5082b8d
```

```
Are you sure you want to delete certificate 99f5fef1-6cc1-46b8-bd79-44a0d5082b8d (my-origin-cert)? [y/n]yesDeleting certificate 99f5fef1-6cc1-46b8-bd79-44a0d5082b8d...Deleted certificate 99f5fef1-6cc1-46b8-bd79-44a0d5082b8d successfully
```

---

## `cert`

[](#cert)

Manage mTLS client certificates and Certificate Authority (CA) chain certificates used for secured connections.

These certificates can be used in Hyperdrive configurations, enabling them to present the certificate when connecting to an origin database that requires client authentication (mTLS) or a custom Certificate Authority (CA).

[](#upload-mtls-certificate)

Upload a client certificate.

```
wrangler cert upload mtls-certificate --cert <PATH> --key <PATH> [OPTIONS]
```

- `--cert` string required
  - A path to the TLS certificate to upload. Certificate chains are supported.
- `--key` string required
  - A path to the private key to upload.
- `--name` string optional
  - The name assigned to the mTLS certificate at upload.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

The following is an example of using the `upload` command to upload an mTLS certificate.

Terminal window ```
npx wrangler cert upload --cert cert.pem --key key.pem --name my-origin-cert
```

```
Uploading mTLS Certificate my-origin-cert...Success! Uploaded mTLS Certificate my-origin-certID: 99f5fef1-6cc1-46b8-bd79-44a0d5082b8dIssuer: CN=my-secured-origin.com,OU=my-team,O=my-org,L=San Francisco,ST=California,C=USExpires: 1/01/2025
```

Note that the certificate and private keys must be in separate (typically `.pem`) files when uploading.

[](#upload-certificate-authority)

Upload a client certificate.

```
wrangler cert upload certificate-authority --ca-cert <PATH> [OPTIONS]
```

- `--ca-cert` string required
  - A path to the Certificate Authority (CA) chain certificate to upload.
- `--name` string optional
  - The name assigned to the mTLS certificate at upload.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

The following is an example of using the `upload` command to upload an CA certificate.

Terminal window ```
npx wrangler cert upload certificate-authority --ca-cert server-ca-chain.pem --name SERVER_CA_CHAIN
```

```
Uploading CA Certificate SERVER_CA_CHAIN...Success! Uploaded CA Certificate SERVER_CA_CHAINID: 99f5fef1-6cc1-46b8-bd79-44a0d5082b8dIssuer: CN=my-secured-origin.com,OU=my-team,O=my-org,L=San Francisco,ST=California,C=USExpires: 1/01/2025
```

### `list`

[](#list-8)

List mTLS certificates associated with the current account ID. This will display both mTLS certificates and CA certificates.

```
wrangler cert list
```

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

The following is an example of using the `list` command to upload an mTLS or CA certificate.

Terminal window ```
npx wrangler cert list
```

```
ID: 99f5fef1-6cc1-46b8-bd79-44a0d5082b8dName: my-origin-certIssuer: CN=my-secured-origin.com,OU=my-team,O=my-org,L=San Francisco,ST=California,C=USCreated on: 1/01/2023Expires: 1/01/2025
ID: c5d004d1-8312-402c-b8ed-6194328d5cbeIssuer: CN=another-origin.com,OU=my-team,O=my-org,L=San Francisco,ST=California,C=USCreated on: 1/01/2023Expires: 1/01/2025
```

### `delete`

[](#delete-7)

Delete a client certificate.

```
wrangler cert delete {--id <ID|--name <NAME>}
```

- `--id` string
  - The ID of the mTLS or CA certificate.
- `--name` string
  - The name assigned to the mTLS or CA certificate at upload.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

The following is an example of using the `delete` command to delete an mTLS or CA certificate.

Terminal window ```
npx wrangler cert delete --id 99f5fef1-6cc1-46b8-bd79-44a0d5082b8d
```

```
Are you sure you want to delete certificate 99f5fef1-6cc1-46b8-bd79-44a0d5082b8d (my-origin-cert)? [y/n]yesDeleting certificate 99f5fef1-6cc1-46b8-bd79-44a0d5082b8d...Deleted certificate 99f5fef1-6cc1-46b8-bd79-44a0d5082b8d successfully
```

---

## `types`

[](#types)

Generate types based on your Worker configuration, including `Env` types based on your bindings, module rules, and [runtime types](/workers/languages/typescript/) based on the `compatibility_date` and `compatibility_flags` in your [config file](/workers/wrangler/configuration/).

```
wrangler types [<PATH>] [OPTIONS]
```

- `PATH` string (default: \`./worker-configuration.d.ts\`)
  - The path to where types for your Worker will be written.
  - The path must have a `d.ts` extension.
- `--env-interface` string (default: \`Env\`)
  - The name of the interface to generate for the environment object.
  - Not valid if the Worker uses the Service Worker syntax.
- `--include-runtime` boolean (default: true)
  - Whether to generate runtime types based on the `compatibility_date` and `compatibility_flags` in your [config file](/workers/wrangler/configuration/).
- `--include-env` boolean (default: true)
  - Whether to generate `Env` types based on your Worker bindings.
- `--strict-vars` boolean optional (default: true)
  - Control the types that Wrangler generates for `vars` bindings.
  - If `true`, (the default) Wrangler generates literal and union types for bindings (e.g. `myVar: 'my dev variable' | 'my prod variable'`).
  - If `false`, Wrangler generates generic types (e.g. `myVar: string`). This is useful when variables change frequently, especially when working across multiple environments.
- `--config`, `-c` string\[\] optional ```
interface Env {  SERVICE_BINDING: Service<import("../bound-worker/src/index").Entrypoint>;}
```
  - Path(s) to [Wrangler configuration file](/workers/wrangler/configuration/). If the Worker you are generating types for has service bindings or bindings to Durable Objects, you can also provide the paths to those configuration files so that the generated `Env` type will include RPC types. For example, given a Worker with a service binding, `wrangler types -c wrangler.toml -c ../bound-worker/wrangler.toml` will generate an `Env` type like this:

---

## `telemetry`

[](#telemetry)

Cloudflare collects anonymous usage data to improve Wrangler. You can learn more about this in our [data policy ↗](https://github.com/cloudflare/workers-sdk/tree/main/packages/wrangler/telemetry.md).

You can manage sharing of usage data at any time using these commands.

### `disable`

[](#disable)

Disable telemetry collection for Wrangler.

```
wrangler telemetry disable
```

### `enable`

[](#enable)

Enable telemetry collection for Wrangler.

```
wrangler telemetry enable
```

### `status`

[](#status-1)

Check whether telemetry collection is currently enabled. The return result is specific to the directory where you have run the command.

This will resolve the global status set by `wrangler telemetry disable / enable`, the environment variable [`WRANGLER_SEND_METRICS`](/workers/wrangler/system-environment-variables/#supported-environment-variables), and the [`send_metrics`](/workers/wrangler/configuration/#top-level-only-keys) key in the [Wrangler configuration file](/workers/wrangler/configuration/).

```
wrangler telemetry status
```

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

---

## `check`

[](#check)

### `startup`

[](#startup)

Generate a CPU profile of your Worker's startup phase.

After you run `wrangler check startup`, you can import the profile into Chrome DevTools or open it directly in VSCode to view a flamegraph of your Worker's startup phase. Additionally, when a Worker deployment fails with a startup time error Wrangler will automatically generate a CPU profile for easy investigation.

Terminal window ```
wrangler check startup
```

- `--args` string optional
  - To customise the way `wrangler check startup` builds your Worker for analysis, provide the exact arguments you use when deploying your Worker with `wrangler deploy`, or your Pages project with `wrangler pages functions build`. For instance, if you deploy your Worker with `wrangler deploy --no-bundle`, you should use `wrangler check startup --args="--no-bundle"` to profile the startup phase.
- `--worker` string optional
  - If you don't use Wrangler to deploy your Worker, you can use this argument to provide a Worker bundle to analyse. This should be a file path to a serialized multipart upload, with the exact same format as [the API expects](/api/resources/workers/subresources/scripts/methods/update/).
- `--pages` boolean optional
  - If you don't use a Wrangler config file with your Pages project (i.e. a Wrangler config file containing `pages_build_output_dir`), use this flag to force `wrangler check startup` to treat your project as a Pages project.

The following global flags work on every command:

- `--help` boolean
  - Show help.
- `--config` string (not supported by Pages)
  - Path to your [Wrangler configuration file](/workers/wrangler/configuration/).
- `--cwd` string
  - Run as if Wrangler was started in the specified directory instead of the current working directory.

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
