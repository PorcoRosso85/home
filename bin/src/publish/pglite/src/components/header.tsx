import { Link } from 'waku';

export const Header = () => {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      gap: '16px',
      padding: '24px'
    }}>
      <h2 style={{
        fontSize: '1.125rem',
        fontWeight: 'bold',
        letterSpacing: '-0.025em',
        fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
      }}>
        <Link to="/">Waku starter</Link>
      </h2>
    </header>
  );
};
