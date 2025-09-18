import { ReactNode } from "react";

type DocumentProps = {
  children: ReactNode;
};

export function Document({ children }: DocumentProps) {
  return (
    <html lang="en">
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>React Transition Demo</title>
        <style>{`
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
          }
          
          .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            margin-right: 8px;
          }
          
          .auth-badge { background-color: #e3f2fd; color: #1976d2; }
          .ssr-badge { background-color: #f3e5f5; color: #7b1fa2; }
          
          .transition-button {
            display: inline-block;
            margin: 8px;
            padding: 12px 16px;
            background-color: #1976d2;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: background-color 0.2s;
          }
          
          .transition-button:hover {
            background-color: #1565c0;
          }
        `}</style>
      </head>
      <body>
        <div id="root">
          {children}
        </div>
        <script type="module" src="/assets/main.js"></script>
      </body>
    </html>
  );
}