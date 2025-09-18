import React from "react";

export function HomePage() {
  return React.createElement(
    "div", 
    { className: "home-page" },
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
      React.createElement("h1", { className: "animate-on-scroll" }, "Welcome to My Static Site!"),
      React.createElement(
        "p", 
        { className: "animate-on-scroll" },
        "This is a static site generated with Deno, React and Vite, with client-side interactivity added through TypeScript."
      ),
      React.createElement(
        "div", 
        { className: "counter-container animate-on-scroll" },
        React.createElement("span", null, "カウンター: "),
        React.createElement("span", { id: "counter" }, "0"),
        React.createElement("button", { id: "increment" }, "増加")
      ),
      React.createElement(
        "div", 
        { className: "feature-section animate-on-scroll" },
        React.createElement("h2", null, "Features"),
        React.createElement(
          "ul", 
          null,
          React.createElement("li", null, "Static Site Generation"),
          React.createElement("li", null, "React Components"),
          React.createElement("li", null, "TypeScript Support"),
          React.createElement("li", null, "Fast Build Times"),
          React.createElement("li", null, "Client-side Interactivity"),
          React.createElement("li", null, "Dark/Light Theme Toggle"),
          React.createElement("li", null, "Vite Development Server"),
          React.createElement("li", null, "Hot Module Replacement")
        )
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