export default function NotFoundPage() {
  return (
    <div style={{
      fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, sans-serif',
      padding: '48px',
      textAlign: 'center'
    }}>
      <h1 style={{ fontSize: '3rem', marginBottom: '16px' }}>404</h1>
      <p style={{ fontSize: '1.25rem', color: '#666' }}>Page not found</p>
    </div>
  );
}

export const getConfig = async () => {
  return {
    render: 'static',
  };
};