import React from "react";
import { Header } from "./Header.tsx";
import { Footer } from "./Footer.tsx";

type LayoutProps = {
  children: React.ReactNode;
  title: string;
};

export function Layout({ children, title }: LayoutProps) {
  return (
    <html lang="en">
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>{title}</title>
        <link rel="stylesheet" href="/styles.css" />
        <link rel="stylesheet" href="/theme.css" />
        {/* TypeScriptはビルド時にJavaScriptに変換されるため、.jsとして参照 */}
        <script src="/js/main.js" defer></script>
      </head>
      <body>
        <div className="theme-toggle-container">
          <button id="theme-toggle">テーマ切替</button>
        </div>
        <Header />
        <main>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
