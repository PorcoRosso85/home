import type { ReactNode } from 'react';

import { Header } from '../components/header';
import { Footer } from '../components/footer';

type RootLayoutProps = { children: ReactNode };

export default async function RootLayout({ children }: RootLayoutProps) {
  const data = await getData();

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <meta name="description" content={data.description} />
      <link rel="icon" type="image/png" href={data.icon} />
      <style>{`
        @font-face {
          font-family: 'GenJyuuGothicL';
          font-style: normal;
          font-weight: 400;
          font-display: swap;
          src: url('https://cdn.jsdelivr.net/gh/ButTaiwan/genjyuugothic@main/GenJyuuGothicL-Regular.ttf') format('truetype');
        }
        @font-face {
          font-family: 'GenJyuuGothicL';
          font-style: normal;
          font-weight: 700;
          font-display: swap;
          src: url('https://cdn.jsdelivr.net/gh/ButTaiwan/genjyuugothic@main/GenJyuuGothicL-Bold.ttf') format('truetype');
        }
        body {
          font-family: 'GenJyuuGothicL', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
      `}</style>
      <Header />
      <main style={{
        flex: 1,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '24px',
        fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
      }}>
        <div style={{ minHeight: '256px', minWidth: '256px' }}>
          {children}
        </div>
      </main>
      <Footer />
    </div>
  );
}

const getData = async () => {
  const data = {
    description: 'An internet website!',
    icon: '/images/favicon.png',
  };

  return data;
};

export const getConfig = async () => {
  return {
    render: 'static',
  } as const;
};
