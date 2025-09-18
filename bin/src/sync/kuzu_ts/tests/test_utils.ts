/**
 * Shared Test Utilities
 * 共有テストユーティリティ
 */

export class TestServer {
  private process: Deno.ChildProcess | null = null;
  private stdout: ReadableStream<Uint8Array> | null = null;
  private stderr: ReadableStream<Uint8Array> | null = null;
  
  async start(port: number = 8080): Promise<void> {
    const denoPath = Deno.env.get("DENO_PATH") || "deno";
    const command = new Deno.Command(denoPath, {
      args: ["run", "--allow-net", "--allow-read", "--allow-env", "./server.ts"],
      stdout: "piped",
      stderr: "piped",
    });
    
    this.process = command.spawn();
    this.stdout = this.process.stdout;
    this.stderr = this.process.stderr;
    
    // stdout/stderrを消費（リーク防止）
    this.consumeStream(this.stdout);
    this.consumeStream(this.stderr);
    
    // サーバー起動を待つ
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  
  private consumeStream(stream: ReadableStream<Uint8Array> | null): void {
    if (!stream) return;
    
    const reader = stream.getReader();
    const read = async () => {
      try {
        while (true) {
          const { done } = await reader.read();
          if (done) break;
        }
      } catch (error) {
        // ストリーム読み取りエラーは無視
      } finally {
        reader.releaseLock();
      }
    };
    read();
  }
  
  async stop(): Promise<void> {
    if (this.process) {
      // Ctrl+Cを送信して正常終了を試みる
      try {
        this.process.kill("SIGTERM");
        await Promise.race([
          this.process.status,
          new Promise(resolve => setTimeout(resolve, 1000))
        ]);
      } catch (error) {
        // エラーは無視
      }
      
      // まだ生きていれば強制終了
      try {
        this.process.kill("SIGKILL");
      } catch (error) {
        // エラーは無視
      }
      
      this.process = null;
      this.stdout = null;
      this.stderr = null;
    }
  }
}

export async function waitForPort(port: number, maxAttempts: number = 10): Promise<boolean> {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const conn = await Deno.connect({ port });
      conn.close();
      return true;
    } catch {
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }
  return false;
}