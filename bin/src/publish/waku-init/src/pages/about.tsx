import { Link } from 'waku';

export default async function AboutPage() {
  const data = await getData();

  return (
    <div style={{
      fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    }}>
      <title>{data.title}</title>
      <h1 style={{
        fontSize: '2.25rem',
        fontWeight: 'bold',
        letterSpacing: '-0.025em',
        fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
      }}>{data.headline}</h1>
      <p>{data.body}</p>
      <Link to="/" style={{
        marginTop: '16px',
        display: 'inline-block',
        textDecoration: 'underline'
      }}>
        Return home
      </Link>
    </div>
  );
}

const getData = async () => {
  const data = {
    title: 'About',
    headline: 'About Waku',
    body: 'The minimal React framework',
  };

  return data;
};

export const getConfig = async () => {
  return {
    render: 'static',
  } as const;
};
