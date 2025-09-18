export const Footer = () => {
  return (
    <footer style={{
      padding: '24px',
      fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    }}>
      <div>
        visit{' '}
        <a
          href="https://waku.gg/"
          target="_blank"
          rel="noreferrer"
          style={{
            textDecoration: 'underline',
            marginTop: '16px',
            display: 'inline-block'
          }}
        >
          waku.gg
        </a>{' '}
        to learn more
      </div>
    </footer>
  );
};
