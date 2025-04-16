import React from "react";

export function AboutPage() {
  return React.createElement(
    "div", 
    { className: "about-page" },
    React.createElement(
      "div", 
      { className: "theme-toggle-container" },
      React.createElement("button", { id: "theme-toggle" }, "テーマ切替")
    ),
    React.createElement(
      "header", 
      { className: "site-header" },
      React.createElement(
        "nav", 
        null,
        React.createElement("a", { href: "/" }, "Home"),
        React.createElement("a", { href: "/about" }, "About"),
        React.createElement("a", { href: "/blog" }, "Blog")
      )
    ),
    React.createElement(
      "main", 
      null,
      React.createElement("h1", { className: "animate-on-scroll" }, "About This Site"),
      React.createElement(
        "p", 
        { className: "animate-on-scroll" },
        "This is a simple static site generated with Deno, React and Vite. It demonstrates how to use JSX/TSX with modern tooling for static site generation."
      ),
      React.createElement(
        "p", 
        { className: "animate-on-scroll" },
        "Built with modern web technologies and served statically for maximum performance. Development is enhanced with Vite for hot module replacement and fast builds."
      )
    ),
    React.createElement(
      "footer", 
      { className: "site-footer" },
      React.createElement(
        "p", 
        null, 
        "\u00A9 ", new Date().getFullYear(), " My Static Site"
      )
    )
  );
}