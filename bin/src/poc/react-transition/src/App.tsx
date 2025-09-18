import React, { useState } from 'react';

// バッジ生成
const getBadges = (config: any = {}) => {
const badges = [];
if (config.auth === true) badges.push('🔒');
if (config.auth === 'guest') badges.push('👤');
badges.push(config.ssr ? '🏗️' : '⚡');
return badges;
};

// 遷移ボタン
const TransitionButton = ({ path, navigate, children }: { path: string; navigate: (path: string) => void; children: React.ReactNode }) => {
const [showTooltip, setShowTooltip] = useState(false);
const config = routes.find(r => r.path === path)?.handler() || {};
const badges = getBadges(config);

return (
<div className="relative inline-block">
<button
onClick={() => navigate(path)}
className="bg-blue-100 hover:bg-blue-200 px-4 py-2 rounded relative"
onMouseEnter={() => setShowTooltip(true)}
onMouseLeave={() => setShowTooltip(false)}
>
{children}
<span className="absolute -top-1 -right-1 text-xs bg-white rounded px-1 border">
{badges.join('')}
</span>
</button>

{showTooltip && (
    <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded py-1 px-2 whitespace-nowrap z-10 tooltip">
      {path} | {config.auth ? (config.auth === 'guest' ? 'ゲスト専用' : '認証必要') : '認証不要'} | {config.ssr ? 'SSR' : 'CSR'}
    </div>
  )}
</div>

);
};

// RedwoodSDK風ルート定義（遷移設計とページ生成を統合）
const route = (path: string, config: any = {}) => ({
path,
handler: () => config
});

// 統合された遷移設計とページ生成
const routes = [
route('/', {
to: ['/login', '/signup', '/products'],
render: (navigate: (path: string) => void) => (
<>
<div className="h-8 bg-gray-200 rounded w-32"></div>
<div className="h-20 bg-gray-100 rounded w-full"></div>
<div className="space-x-2">
<TransitionButton path="/login" navigate={navigate}>Login</TransitionButton>
<TransitionButton path="/signup" navigate={navigate}>Signup</TransitionButton>
<TransitionButton path="/products" navigate={navigate}>Products</TransitionButton>
</div>
</>
)
}),

route('/login', {
to: ['/dashboard'],
auth: 'guest',
ssr: true,
render: (navigate: (path: string) => void) => (
<>
<div className="h-8 bg-gray-200 rounded w-32"></div>
<div className="h-10 bg-gray-100 rounded w-full"></div>
<div className="h-10 bg-gray-100 rounded w-full"></div>
<TransitionButton path="/dashboard" navigate={navigate}>Submit</TransitionButton>
</>
)
}),

route('/signup', {
to: ['/dashboard'],
auth: 'guest',
render: (navigate: (path: string) => void) => (
<>
<div className="h-8 bg-gray-200 rounded w-32"></div>
<div className="h-10 bg-gray-100 rounded w-full"></div>
<div className="h-10 bg-gray-100 rounded w-full"></div>
<div className="h-10 bg-gray-100 rounded w-full"></div>
<TransitionButton path="/dashboard" navigate={navigate}>Create Account</TransitionButton>
</>
)
}),

route('/products', {
to: ['/product/[id]'],
parent: '/',
render: (navigate: (path: string) => void) => (
<>
<div className="h-8 bg-gray-200 rounded w-32"></div>
{[1, 2, 3].map(id => (
<div key={id} className="border p-4 rounded space-y-2">
<div className="h-6 bg-gray-200 rounded w-48"></div>
<TransitionButton path={`/product/${id}`} navigate={navigate}>View</TransitionButton>
</div>
))}
</>
)
}),

route('/product/[id]', {
to: ['/product/[id]/edit'],
auth: true,
parent: '/products',
render: (navigate: (path: string) => void, { path }: { path: string }) => (
<>
<div className="h-8 bg-gray-200 rounded w-32"></div>
<div className="h-32 bg-gray-100 rounded w-full"></div>
<TransitionButton path={`${path}/edit`} navigate={navigate}>Edit</TransitionButton>
</>
)
}),

route('/product/[id]/edit', {
to: ['/product/[id]'],
auth: true,
ssr: true,
parent: '/product/[id]',
render: (navigate: (path: string) => void, { path }: { path: string }) => (
<>
<div className="h-8 bg-gray-200 rounded w-32"></div>
<div className="h-10 bg-gray-100 rounded w-full"></div>
<div className="h-20 bg-gray-100 rounded w-full"></div>
<TransitionButton path={path.replace('/edit', '')} navigate={navigate}>Save</TransitionButton>
</>
)
}),

route('/dashboard', {
to: ['/products'],
auth: true,
render: (navigate: (path: string) => void) => (
<>
<div className="h-8 bg-gray-200 rounded w-32"></div>
<div className="grid grid-cols-2 gap-4">
<div className="h-24 bg-blue-100 rounded"></div>
<div className="h-24 bg-green-100 rounded"></div>
</div>
<TransitionButton path="/products" navigate={navigate}>View Products</TransitionButton>
</>
)
})
];

// ページレンダリング
const renderPage = (path: string, navigate: (path: string) => void) => {
const parseRoute = (path: string) => {
const match = path.match(/^\/product\/(\d+)(?:\/(edit))?$/);
return match ? (match[2] ? '/product/[id]/edit' : '/product/[id]') : path;
};

const routePath = parseRoute(path);
const route = routes.find(r => r.path === routePath);

return (
<div className="p-8 space-y-4">
{route?.handler().render ? route.handler().render(navigate, { path }) : (
<div className="text-red-600">404 - Page Not Found</div>
)}
</div>
);
};

const App = () => {
const [route, setRoute] = useState('/');

return (
<div className="min-h-screen bg-gray-50">
{/* 遷移設計表示 */}
<div className="bg-yellow-50 border-b p-2 text-xs">
<details className="cursor-pointer">
<summary className="font-bold">🗺️ 遷移設計 (クリックで表示)</summary>
<div className="mt-2 space-y-1">
{routes.map(({ path, handler }) => {
const config = handler();
return (
<div key={path} className="flex items-center space-x-2">
<code className="bg-white px-2 py-1 rounded">{path}</code>
<span>→</span>
<div className="flex space-x-1">
{(config.to || []).map((to: string) => (
<code key={to} className="bg-blue-50 px-1 rounded text-blue-700">{to}</code>
))}
</div>
<span className="text-gray-500">{getBadges(config).join('')}</span>
</div>
);
})}
</div>
</details>
</div>

{/* パンくず breadcrumb navigation */}
  <nav className="bg-white border-b p-4">
    <div className="flex items-center space-x-2 text-sm">
      {route.split('/').filter(Boolean).reduce((acc: React.ReactNode[], segment, i, arr) => {
        const path = '/' + arr.slice(0, i + 1).join('/');
        const isLast = i === arr.length - 1;
        
        if (i > 0) acc.push(<span key={`sep-${i}`} className="text-gray-400">/</span>);
        acc.push(
          <button
            key={path}
            onClick={() => setRoute(path)}
            className={isLast ? 'text-gray-800 font-medium' : 'text-blue-600 hover:text-blue-800'}
          >
            {segment}
          </button>
        );
        return acc;
      }, [
        <button
          key="home"
          onClick={() => setRoute('/')}
          className={route === '/' ? 'text-gray-800 font-medium' : 'text-blue-600 hover:text-blue-800'}
        >
          home
        </button>
      ])}
    </div>
  </nav>
  
  {renderPage(route, setRoute)}
</div>

);
};

export default App;