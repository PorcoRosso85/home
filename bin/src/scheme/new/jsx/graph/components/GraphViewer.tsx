// GraphViewer.tsx - グラフ表示コンポーネント
import React, { useEffect, useRef, useState } from "https://esm.sh/react@18.2.0";
import * as d3 from "https://esm.sh/d3@7.8.5";
import { GraphData } from "../types/types";
import { nodeTypeColors, statusColors } from "../utils/colors";

interface GraphViewerProps {
  graphData: GraphData;
  onNodeSelect: (nodeId: string) => void;
}

const GraphViewer: React.FC<GraphViewerProps> = ({ graphData, onNodeSelect }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dimensions, setDimensions] = useState({ width: window.innerWidth, height: window.innerHeight });
  
  // リサイズハンドラー
  useEffect(() => {
    const handleResize = () => {
      setDimensions({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);
  
  // グラフレンダリング
  useEffect(() => {
    if (!svgRef.current || !graphData) return;
    
    // SVG要素の参照を取得
    const svg = d3.select(svgRef.current);
    
    // 以前の内容をクリア
    svg.selectAll('*').remove();
    
    // ノードとリンクのデータを準備
    const nodes = Object.values(graphData.nodes);
    const links = graphData.edges.map(edge => ({
      ...edge,
      source: edge.source,
      target: edge.target
    }));
    
    // シミュレーションを作成
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links)
        .id(d => d.id)
        .distance(150))
      .force('charge', d3.forceManyBody().strength(-500))
      .force('center', d3.forceCenter(dimensions.width / 2, dimensions.height / 2))
      .force('collision', d3.forceCollide().radius(60));
    
    // ズーム機能を追加
    const zoom = d3.zoom()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });
    
    svg.call(zoom);
    
    // コンテナグループを作成
    const container = svg.append('g');
    
    // マーカー（矢印）の定義
    svg.append('defs').selectAll('marker')
      .data(['end'])
      .enter().append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 25)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#999');
      
    // エッジの描画
    const link = container.append('g')
      .selectAll('g')
      .data(links)
      .enter()
      .append('g');
    
    // エッジのライン
    link.append('path')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 2)
      .attr('fill', 'none')
      .attr('marker-end', 'url(#arrow)');
    
    // エッジのラベル
    link.append('text')
      .attr('class', 'edge-label')
      .attr('dy', -8)
      .attr('text-anchor', 'middle')
      .attr('fill', '#666')
      .attr('font-size', '12px')
      .text(d => d.name);
    
    // ノードの描画
    const node = container.append('g')
      .selectAll('.node')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'node')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended))
      .on('click', (event, d) => {
        onNodeSelect(d.id);
        event.stopPropagation();
      });
    
    // ノードの円
    node.append('circle')
      .attr('r', 35)
      .attr('fill', d => nodeTypeColors[d.type] || '#ccc')
      .attr('stroke', d => statusColors[d?.metadata?.implementation?.status] || '#333')
      .attr('stroke-width', 3)
      .attr('cursor', 'pointer');
    
    // 開発中ノードの点線円（パルスアニメーション）
    node.filter(d => d?.metadata?.implementation?.status === '開発中' || d?.metadata?.implementation?.status === 'テスト中')
      .append('circle')
      .attr('r', 40)
      .attr('fill', 'none')
      .attr('stroke', d => statusColors[d?.metadata?.implementation?.status] || '#333')
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '5,5')
      .attr('opacity', 0.6)
      .attr('class', 'pulse-circle');
    
    // スタイル要素を追加
    const style = document.createElement('style');
    style.textContent = `
      @keyframes pulse {
        0% { transform: scale(1); opacity: 0.6; }
        50% { transform: scale(1.1); opacity: 0.3; }
        100% { transform: scale(1); opacity: 0.6; }
      }
      .pulse-circle {
        animation: pulse 2s infinite ease-in-out;
      }
    `;
    document.head.appendChild(style);
    
    // ノード名ラベル
    node.append('text')
      .attr('dy', -45)
      .attr('text-anchor', 'middle')
      .attr('fill', '#333')
      .attr('font-size', '14px')
      .attr('font-weight', 'bold')
      .text(d => d.name);
    
    // ノードIDラベル
    node.append('text')
      .attr('dy', 48)
      .attr('text-anchor', 'middle')
      .attr('fill', '#666')
      .attr('font-size', '12px')
      .text(d => d.id);
    
    // 進捗バー背景
    node.append('rect')
      .attr('x', -25)
      .attr('y', 20)
      .attr('width', 50)
      .attr('height', 6)
      .attr('fill', '#eee')
      .attr('rx', 3)
      .attr('ry', 3);
    
    // 進捗バー
    node.append('rect')
      .attr('x', -25)
      .attr('y', 20)
      .attr('height', 6)
      .attr('fill', d => {
        const progress = d?.metadata?.implementation?.progress || 0;
        if (progress < 30) return '#e74c3c';
        if (progress < 70) return '#f39c12';
        return '#2ecc71';
      })
      .attr('rx', 3)
      .attr('ry', 3)
      .attr('width', d => ((d?.metadata?.implementation?.progress || 0) / 100) * 50);
    
    // ツールチップの追加
    node.append('title')
      .text(d => {
        const status = d?.metadata?.implementation?.status || '未設定';
        const progress = d?.metadata?.implementation?.progress || 0;
        return `${d.name}\n${d.type}\n${d.description}\nステータス: ${status}\n進捗: ${progress}%`;
      });
    
    // シミュレーションの更新処理
    simulation.on('tick', () => {
      // エッジのパスを更新
      link.selectAll('path.link')
        .attr('d', d => {
          const sourceX = d.source.x;
          const sourceY = d.source.y;
          const targetX = d.target.x;
          const targetY = d.target.y;
          
          // 始点と終点の距離を計算
          const dx = targetX - sourceX;
          const dy = targetY - sourceY;
          const dr = Math.sqrt(dx * dx + dy * dy);
          
          // 接線の角度を計算
          const theta = Math.atan2(dy, dx);
          
          // ノードの半径を考慮して始点と終点を調整
          const sourceNodeRadius = 35;
          const targetNodeRadius = 35;
          
          const sourceXAdjusted = sourceX + (sourceNodeRadius * Math.cos(theta));
          const sourceYAdjusted = sourceY + (sourceNodeRadius * Math.sin(theta));
          const targetXAdjusted = targetX - (targetNodeRadius * Math.cos(theta));
          const targetYAdjusted = targetY - (targetNodeRadius * Math.sin(theta));
          
          return `M${sourceXAdjusted},${sourceYAdjusted}L${targetXAdjusted},${targetYAdjusted}`;
        });
      
      // エッジラベルの位置更新
      link.selectAll('text.edge-label')
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2);
      
      // ノードの位置更新
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
    
    // ドラッグ開始時の処理
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    
    // ドラッグ中の処理
    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }
    
    // ドラッグ終了時の処理
    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
    
    // クリーンアップ
    return () => {
      simulation.stop();
    };
  }, [graphData, dimensions, onNodeSelect]);
  
  return (
    <div style={{ width: "100%", height: "100%", position: "absolute", top: 0, left: 0 }}>
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        style={{ background: "white" }}
      ></svg>
    </div>
  );
};

export default GraphViewer;
