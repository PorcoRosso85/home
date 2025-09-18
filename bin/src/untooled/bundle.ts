#!/usr/bin/env -S nix shell nixpkgs#deno --command deno run --allow-all
import $ from "jsr:@david/dax";
import {bundleMDX} from 'npm:mdx-bundler'
import {getMDXComponent} from 'npm:mdx-bundler/client'
import * as React from 'npm:react'

async function main() {

  const mdxSource = `
  ---
  title: Example Post
  published: 2021-02-13
  description: This is some description
  ---

  # Wahoo

  import Demo from './demo'

  Here's a **neat** demo:

  <Demo />
  `.trim()

  const result = await bundleMDX({
    source: mdxSource,
    files: {
      './demo.tsx': `
  import * as React from 'react'

  function Demo() {
    return <div>Neat demo!</div>
  }

  export default Demo
      `,
    },
  })

  const {code, frontmatter} = result

  function Post({code, frontmatter}) {
    // it's generally a good idea to memoize this function call to
    // avoid re-creating the component every render.
    const Component = React.useMemo(() => getMDXComponent(code), [code])
    return (
      <>
        <header>
          <h1>{frontmatter.title}</h1>
          <p>{frontmatter.description}</p>
        </header>
        <main>
          <Component />
        </main>
      </>
    )
  }
}


await main();
