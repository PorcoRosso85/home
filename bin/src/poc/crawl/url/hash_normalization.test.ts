import {
  assert,
  assertEquals,
  assertExists,
} from "https://deno.land/std@0.224.0/assert/mod.ts";
import {
  URLCrawler,
} from "./crawl.ts";

// ハッシュリンクの正規化テスト
Deno.test("URLCrawler - ハッシュフラグメントの正規化", async (t) => {
  const port = 8765;
  
  const handler = (req: Request): Response => {
    const url = new URL(req.url);
    
    if (url.pathname === "/") {
      return new Response(`
        <!DOCTYPE html>
        <html>
        <body>
          <a href="#section1">Section 1</a>
          <a href="#section2">Section 2</a>
          <a href="/page#hash">Page with hash</a>
          <a href="/page">Same page without hash</a>
          <a href="/another#part1">Another page part 1</a>
          <a href="/another#part2">Another page part 2</a>
        </body>
        </html>
      `, { headers: { "content-type": "text/html" } });
    }
    
    return new Response("Not Found", { status: 404 });
  };
  
  const server = Deno.serve({ port, onListen: () => {} }, handler);
  
  try {
    await new Promise(resolve => setTimeout(resolve, 100));
    
    await t.step("同じページの異なるハッシュは重複として除外される", async () => {
      const crawler = new URLCrawler(`http://localhost:${port}`);
      const results = await crawler.crawl();
      
      const rootResult = results.find(r => r.url === `http://localhost:${port}`);
      assertExists(rootResult);
      
      // ハッシュが除去されているため、重複が削除される
      const links = rootResult.links;
      console.log("抽出されたリンク:", links);
      
      // #section1, #section2 は同じページ（/）として扱われ、リンクには含まれる
      assertEquals(links.filter(l => l === `http://localhost:${port}/`).length, 1);
      
      // /pageは1つだけ（#hashありとなしが統合される）
      assertEquals(links.filter(l => l === `http://localhost:${port}/page`).length, 1);
      
      // /anotherも1つだけ（#part1と#part2が統合される）
      assertEquals(links.filter(l => l === `http://localhost:${port}/another`).length, 1);
      
      // 全体で3つのユニークなリンク（/, /page, /another）
      assertEquals(links.length, 3);
    });
    
    await t.step("クロール結果にハッシュが含まれない", async () => {
      const crawler = new URLCrawler(`http://localhost:${port}`);
      const results = await crawler.crawl();
      
      // すべてのURLにハッシュが含まれていないことを確認
      for (const result of results) {
        assert(!result.url.includes('#'), `URL should not contain hash: ${result.url}`);
        for (const link of result.links) {
          assert(!link.includes('#'), `Link should not contain hash: ${link}`);
        }
      }
    });
  } finally {
    await server.shutdown();
  }
});