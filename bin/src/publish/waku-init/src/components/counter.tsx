'use client';

import { useState } from 'react';

export const Counter = ({ max }: { max?: number | undefined }) => {
  const [count, setCount] = useState(0);

  const handleIncrement = () =>
    setCount((c) => (max !== undefined && c + 1 > max ? c : c + 1));

  return (
    <section style={{
      border: '1px dashed #60a5fa',
      borderRadius: '2px',
      marginTop: '16px',
      marginLeft: '-16px',
      marginRight: '-16px',
      padding: '16px',
      fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    }}>
      <div>Count: {count}</div>
      <button
        onClick={handleIncrement}
        style={{
          backgroundColor: 'black',
          color: 'white',
          paddingLeft: '8px',
          paddingRight: '8px',
          paddingTop: '2px',
          paddingBottom: '2px',
          fontSize: '0.875rem',
          borderRadius: '2px',
          border: 'none',
          cursor: 'pointer'
        }}
      >
        Increment
      </button>
    </section>
  );
};
