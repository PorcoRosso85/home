'use client';

import { useState } from 'react';

export const DonutChart = () => {
  const data = [
    { label: 'React', value: 35, color: '#61dafb' },
    { label: 'Vue', value: 25, color: '#4fc08d' },
    { label: 'Angular', value: 20, color: '#dd0031' },
    { label: 'Svelte', value: 20, color: '#ff3e00' }
  ];

  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const total = data.reduce((sum, item) => sum + item.value, 0);
  const centerX = 100;
  const centerY = 100;
  const radius = 80;
  const innerRadius = 50;

  let cumulativeAngle = -90; // Start from top

  const createPath = (value: number) => {
    const angle = (value / total) * 360;
    const startAngle = (cumulativeAngle * Math.PI) / 180;
    const endAngle = ((cumulativeAngle + angle) * Math.PI) / 180;
    cumulativeAngle += angle;

    const largeArcFlag = angle > 180 ? 1 : 0;

    const x1 = centerX + radius * Math.cos(startAngle);
    const y1 = centerY + radius * Math.sin(startAngle);
    const x2 = centerX + radius * Math.cos(endAngle);
    const y2 = centerY + radius * Math.sin(endAngle);

    const ix1 = centerX + innerRadius * Math.cos(startAngle);
    const iy1 = centerY + innerRadius * Math.sin(startAngle);
    const ix2 = centerX + innerRadius * Math.cos(endAngle);
    const iy2 = centerY + innerRadius * Math.sin(endAngle);

    return `
      M ${x1} ${y1}
      A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}
      L ${ix2} ${iy2}
      A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${ix1} ${iy1}
      Z
    `;
  };

  cumulativeAngle = -90; // Reset for rendering

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
      <h3 style={{ margin: 0, marginBottom: '16px', fontSize: '1.125rem' }}>
        Framework Usage Donut Chart
      </h3>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
        <svg width="200" height="200" viewBox="0 0 200 200">
          {data.map((item, index) => {
            const path = createPath(item.value);
            return (
              <path
                key={index}
                d={path}
                fill={item.color}
                stroke="white"
                strokeWidth="2"
                opacity={hoveredIndex === null || hoveredIndex === index ? 1 : 0.6}
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
                style={{ cursor: 'pointer', transition: 'opacity 0.2s' }}
              />
            );
          })}
          
          <text
            x={centerX}
            y={centerY}
            textAnchor="middle"
            dominantBaseline="middle"
            style={{
              fontSize: '24px',
              fontWeight: 'bold',
              fill: '#333',
              fontFamily: '"GenJyuuGothicL", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            }}
          >
            {total}%
          </text>
        </svg>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {data.map((item, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                opacity: hoveredIndex === null || hoveredIndex === index ? 1 : 0.6,
                cursor: 'pointer',
                transition: 'opacity 0.2s'
              }}
              onMouseEnter={() => setHoveredIndex(index)}
              onMouseLeave={() => setHoveredIndex(null)}
            >
              <div style={{
                width: '16px',
                height: '16px',
                backgroundColor: item.color,
                borderRadius: '2px'
              }} />
              <span style={{ fontSize: '0.875rem' }}>
                {item.label}: {item.value}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};