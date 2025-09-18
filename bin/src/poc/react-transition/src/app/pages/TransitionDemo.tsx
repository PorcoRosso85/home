"use client";

import { useState } from "react";

// Route definitions with authentication and SSR metadata
const routes = [
  { path: '/', name: 'Home', auth: false, ssr: true, description: 'Public landing page' },
  { path: '/admin/settings', name: 'Admin Settings', auth: true, ssr: false, description: 'Admin configuration panel' },
  { path: '/user/profile', name: 'User Profile', auth: true, ssr: true, description: 'User profile management' },
  { path: '/api/data', name: 'API Data', auth: false, ssr: false, description: 'Data API endpoint' },
  { path: '/blog/article', name: 'Blog Article', auth: false, ssr: true, description: 'Blog post content' },
  { path: '/dashboard', name: 'Dashboard', auth: true, ssr: false, description: 'User dashboard' },
];

function Badge({ type, children }: { type: 'auth' | 'ssr', children: React.ReactNode }) {
  return (
    <span className={`badge ${type}-badge`}>
      {children}
    </span>
  );
}

function TransitionButton({ route, currentPath, onNavigate }: { 
  route: typeof routes[0], 
  currentPath: string, 
  onNavigate: (path: string) => void 
}) {
  const isActive = currentPath === route.path;
  
  return (
    <button
      className={`transition-button ${isActive ? 'active' : ''}`}
      onClick={() => onNavigate(route.path)}
      style={{
        backgroundColor: isActive ? '#1565c0' : '#1976d2',
        opacity: isActive ? 0.8 : 1,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span>{route.name}</span>
        <div>
          {route.auth && <Badge type="auth">🔒 Auth</Badge>}
          {route.ssr && <Badge type="ssr">⚡ SSR</Badge>}
        </div>
      </div>
    </button>
  );
}

export function TransitionDemo() {
  const [currentPath, setCurrentPath] = useState('/');
  
  const currentRoute = routes.find(r => r.path === currentPath) || routes[0];
  
  // Generate breadcrumb navigation
  const pathSegments = currentPath.split('/').filter(Boolean);
  const breadcrumbs = ['Home', ...pathSegments.map(segment => 
    segment.charAt(0).toUpperCase() + segment.slice(1)
  )];

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1>🚀 React Transition Demo (Worker × RSC)</h1>
      <p style={{ color: '#666', marginBottom: '32px' }}>
        Interactive screen transition demonstration powered by Cloudflare Workers and React Server Components.
        Click buttons to experience different navigation patterns with authentication and SSR states.
      </p>

      {/* Breadcrumb Navigation */}
      <div style={{ 
        padding: '12px 16px', 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        marginBottom: '24px',
        border: '1px solid #e0e0e0'
      }}>
        <strong>Navigation Path:</strong> {breadcrumbs.join(' > ')}
      </div>

      {/* Current Route Info */}
      <div style={{ 
        padding: '16px', 
        backgroundColor: 'white', 
        borderRadius: '8px', 
        marginBottom: '24px',
        border: '1px solid #e0e0e0'
      }}>
        <h3 style={{ margin: '0 0 8px 0', color: '#1976d2' }}>
          Current: {currentRoute.name}
        </h3>
        <p style={{ margin: '0 0 12px 0', color: '#666' }}>
          {currentRoute.description}
        </p>
        <div>
          <Badge type="auth">{currentRoute.auth ? '🔒 Authentication Required' : '👤 Public Access'}</Badge>
          <Badge type="ssr">{currentRoute.ssr ? '⚡ Server-Side Rendered' : '🏗️ Client-Side Rendered'}</Badge>
        </div>
      </div>

      {/* Transition Buttons */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
        gap: '16px',
        marginBottom: '32px'
      }}>
        {routes.map((route) => (
          <TransitionButton
            key={route.path}
            route={route}
            currentPath={currentPath}
            onNavigate={setCurrentPath}
          />
        ))}
      </div>

      {/* Implementation Notes */}
      <div style={{ 
        padding: '16px', 
        backgroundColor: '#f8f9fa', 
        borderRadius: '8px', 
        fontSize: '14px',
        color: '#666'
      }}>
        <strong>🏗️ Technical Implementation:</strong>
        <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
          <li><strong>Server Components:</strong> Initial HTML rendered on Cloudflare Workers</li>
          <li><strong>Client Hydration:</strong> Interactive transitions powered by React 19</li>
          <li><strong>Edge Runtime:</strong> Global distribution for optimal performance</li>
          <li><strong>Badge System:</strong> Visual indicators for auth/SSR requirements</li>
        </ul>
      </div>
    </div>
  );
}