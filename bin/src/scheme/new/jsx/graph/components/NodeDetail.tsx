// NodeDetail.tsx - ノード詳細表示コンポーネント
import React from "https://esm.sh/react@18.2.0";
import { Node, Edge, DocumentationReference } from "../types/types";
import { getProgressColor, getStatusStyle } from "../utils/colors";
import { ReferenceIcon } from "./icons/ReferenceIcons";

interface NodeDetailProps {
  node: Node;
  relatedEdges: Edge[];
  onClose: () => void;
}

const NodeDetail: React.FC<NodeDetailProps> = ({ node, relatedEdges, onClose }) => {
  if (!node) return null;
  
  // スタイル定義
  const styles = {
    container: {
      backgroundColor: 'white',
      borderRadius: '8px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
      padding: '16px',
      marginTop: '16px',
      position: 'absolute',
      bottom: '20px',
      right: '20px',
      width: '400px',
      maxHeight: '80vh',
      overflowY: 'auto',
      zIndex: 1000
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '16px',
      paddingBottom: '8px',
      borderBottom: '1px solid #e5e7eb'
    },
    title: {
      fontSize: '18px',
      fontWeight: 600,
      color: '#111827'
    },
    closeButton: {
      background: 'none',
      border: 'none',
      cursor: 'pointer',
      color: '#9ca3af'
    },
    section: {
      marginBottom: '16px'
    },
    sectionTitle: {
      fontSize: '14px',
      fontWeight: 500,
      color: '#4b5563',
      marginBottom: '8px'
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(2, 1fr)',
      gap: '16px'
    },
    dl: {
      margin: 0
    },
    dt: {
      fontSize: '12px',
      fontWeight: 500,
      color: '#6b7280',
      marginBottom: '4px'
    },
    dd: {
      fontSize: '14px',
      color: '#111827',
      margin: 0,
      marginBottom: '8px'
    },
    tagContainer: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: '4px'
    },
    tag: {
      background: '#dbeafe',
      color: '#1e40af',
      padding: '2px 8px',
      borderRadius: '9999px',
      fontSize: '12px'
    },
    progressContainer: {
      background: '#f3f4f6',
      borderRadius: '9999px',
      height: '8px',
      overflow: 'hidden',
      marginTop: '4px'
    },
    progressBar: {
      height: '100%',
      borderRadius: '9999px'
    },
    progressText: {
      fontSize: '12px',
      color: '#6b7280',
      marginTop: '4px'
    },
    schemaContainer: {
      background: '#f9fafb',
      padding: '12px',
      borderRadius: '6px',
      overflow: 'auto',
      maxHeight: '200px',
      fontSize: '12px',
      fontFamily: 'monospace',
      marginTop: '8px',
      gridColumn: 'span 2'
    },
    table: {
      width: '100%',
      borderCollapse: 'collapse',
      fontSize: '14px',
      gridColumn: 'span 2'
    },
    th: {
      textAlign: 'left',
      padding: '8px 12px',
      fontSize: '12px',
      fontWeight: 500,
      color: '#6b7280',
      borderBottom: '1px solid #e5e7eb',
      backgroundColor: '#f9fafb'
    },
    td: {
      padding: '8px 12px',
      borderBottom: '1px solid #e5e7eb'
    },
    refLink: {
      display: 'inline-flex',
      alignItems: 'center',
      color: '#2563eb',
      textDecoration: 'none',
      marginRight: '8px',
      fontSize: '12px'
    }
  };
  
  // 実装情報の取得
  const implementation = node.metadata?.implementation;
  const documentation = node.metadata?.documentation || [];
  
  // 実装に関する処理を行うレンダリング関数
  const renderImplementation = () => {
    if (!implementation) return null;
    
    return (
      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>実装状況</h3>
        <dl style={styles.dl}>
          <dt style={styles.dt}>ステータス</dt>
          <dd style={styles.dd}>
            <span style={getStatusStyle(implementation.status)}>
              {implementation.status}
            </span>
          </dd>
          
          {implementation.assignee && (
            <>
              <dt style={styles.dt}>担当者</dt>
              <dd style={styles.dd}>{implementation.assignee}</dd>
            </>
          )}
          
          <dt style={styles.dt}>進捗</dt>
          <dd style={styles.dd}>
            <div style={styles.progressContainer}>
              <div 
                style={{
                  ...styles.progressBar,
                  width: `${implementation.progress}%`,
                  backgroundColor: getProgressColor(implementation.progress)
                }}
              ></div>
            </div>
            <span style={styles.progressText}>{implementation.progress}%</span>
          </dd>
          
          {implementation.notes && (
            <>
              <dt style={styles.dt}>備考</dt>
              <dd style={styles.dd}>{implementation.notes}</dd>
            </>
          )}
          
          {implementation.issues && implementation.issues.length > 0 && (
            <>
              <dt style={styles.dt}>課題</dt>
              <dd style={styles.dd}>
                <ul style={{ margin: 0, paddingLeft: '16px' }}>
                  {implementation.issues.map((issue, index) => (
                    <li key={index} style={{ fontSize: '12px' }}>{issue}</li>
                  ))}
                </ul>
              </dd>
            </>
          )}
          
          {implementation.location && (
            <>
              <dt style={styles.dt}>実装場所</dt>
              <dd style={styles.dd}>
                <code style={{ fontSize: '12px', backgroundColor: '#f3f4f6', padding: '2px 4px', borderRadius: '4px' }}>
                  {implementation.location.protocol}://{implementation.location.path}
                </code>
              </dd>
            </>
          )}
        </dl>
      </div>
    );
  };
  
  // ドキュメント参照を表示する関数
  const renderDocumentation = () => {
    if (documentation.length === 0) return null;
    
    return (
      <div style={{ ...styles.section, gridColumn: 'span 2' }}>
        <h3 style={styles.sectionTitle}>ドキュメント</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {documentation.map((doc: DocumentationReference, index: number) => (
            <a 
              key={index}
              href={doc.url}
              target="_blank"
              rel="noopener noreferrer"
              style={styles.refLink}
            >
              <ReferenceIcon type={doc.type} />
              <span style={{ marginLeft: '4px' }}>{doc.title}</span>
            </a>
          ))}
        </div>
      </div>
    );
  };
  
  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>{node.name}</h2>
        <button onClick={onClose} style={styles.closeButton}>
          <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div style={styles.grid}>
        {/* 基本情報 */}
        <div style={styles.section}>
          <h3 style={styles.sectionTitle}>基本情報</h3>
          <dl style={styles.dl}>
            <dt style={styles.dt}>ID</dt>
            <dd style={styles.dd}>{node.id}</dd>
            
            <dt style={styles.dt}>タイプ</dt>
            <dd style={styles.dd}>{node.type}</dd>
            
            <dt style={styles.dt}>説明</dt>
            <dd style={styles.dd}>{node.description}</dd>
            
            <dt style={styles.dt}>タグ</dt>
            <dd style={styles.dd}>
              <div style={styles.tagContainer}>
                {node.tags.map((tag, index) => (
                  <span key={index} style={styles.tag}>{tag}</span>
                ))}
              </div>
            </dd>
          </dl>
        </div>

        {/* 実装ステータス */}
        {renderImplementation()}

        {/* ドキュメント */}
        {renderDocumentation()}

        {/* スキーマ情報 */}
        <div style={{ ...styles.section, gridColumn: 'span 2' }}>
          <h3 style={styles.sectionTitle}>スキーマ定義</h3>
          <div style={styles.schemaContainer}>
            <pre style={{ margin: 0 }}>
              {JSON.stringify(node.schema, null, 2)}
            </pre>
          </div>
        </div>

        {/* 関連エッジ */}
        {relatedEdges.length > 0 && (
          <div style={{ ...styles.section, gridColumn: 'span 2' }}>
            <h3 style={styles.sectionTitle}>関連する処理</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>処理名</th>
                    <th style={styles.th}>方向</th>
                    <th style={styles.th}>接続先</th>
                    <th style={styles.th}>ステータス</th>
                    <th style={styles.th}>タイプ</th>
                  </tr>
                </thead>
                <tbody>
                  {relatedEdges.map((edge) => (
                    <tr key={edge.id}>
                      <td style={styles.td}>{edge.name}</td>
                      <td style={styles.td}>
                        {edge.source === node.id ? '出力' : '入力'}
                      </td>
                      <td style={styles.td}>
                        {edge.source === node.id
                          ? edge.target
                          : edge.source}
                      </td>
                      <td style={styles.td}>
                        <span style={getStatusStyle(edge.metadata?.implementation?.status || '')}>
                          {edge.metadata?.implementation?.status || '未設定'}
                        </span>
                      </td>
                      <td style={styles.td}>
                        <span style={{ color: '#6b7280', fontSize: '12px' }}>
                          {edge.type || '未設定'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NodeDetail;
