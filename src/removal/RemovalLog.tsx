import React, { useEffect, useRef, useState } from 'react';
type LogLine = {
  id: string;
  ts: string;
  level: 'info'|'warn'|'error'|'debug';
  message: string;
  site?: string;
};
type Reasoning = {
  goal: string;
  approach: string;
  constraints: string[];
  lastNote?: string;
};
const levelColor: Record<LogLine['level'], string> = {
  info: '#0b74e5',
  warn: '#f59e0b',
  error: '#ef4444',
  debug: '#6b7280',
};
export const RemovalLogScreen: React.FC = () => {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [currentSite, setCurrentSite] = useState<string | undefined>(undefined);
  const [paused, setPaused] = useState(false);
  const [reasoning, setReasoning] = useState<Reasoning>({
    goal: 'Safely remove targeted items from the page',
    approach: 'Walk the DOM-like structure, identify removable blocks, test non-destructive actions',
    constraints: ['Do not modify visible content unexpectedly', 'Respect site structure'],
  });
  const endRef = useRef<HTMLDivElement | null>(null);
  // Mock real-time feed (replace with live feed later)
  useEffect(() => {
    const sites = [
      'https://example.com/removals',
      'https://site2.org/content',
      'https://site3.net/profile'
    ];
    let i = 0;
    const id = setInterval(() => {
      if (paused) return;
      const site = sites[i % sites.length];
      const line: LogLine = {
        id: `${Date.now()}-${i}`,
        ts: new Date().toLocaleTimeString(),
        level: i % 5 === 0 ? 'warn' : (i % 7 === 0 ? 'debug' : 'info'),
        message: `Navigated to ${site} | inspecting elements`,
        site
      };
      setCurrentSite(site);
      setLogs((l) => [...l, line]);
      i++;
    }, 1200);
    return () => clearInterval(id);
  }, [paused]);
  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (!paused && endRef.current) {
      endRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, paused]);
  const clearLogs = () => setLogs([]);
  const togglePause = () => setPaused((p) => !p);
  const containerStyle: React.CSSProperties = {
    display: 'flex',
    flexDirection: 'row',
    gap: 16,
    height: '100%',
  };
  const leftStyle: React.CSSProperties = {
    flex: 1,
    minWidth: 320,
    display: 'flex',
    flexDirection: 'column',
    borderRadius: 12,
    border: '1px solid #e5e7eb',
    overflow: 'hidden',
    background: '#fff',
    boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
  };
  const rightStyle: React.CSSProperties = {
    width: 360,
    minWidth: 300,
    display: 'flex',
    flexDirection: 'column',
    borderRadius: 12,
    border: '1px solid #e5e7eb',
    padding: 12,
    background: '#fff',
    boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
  };
  const headerStyle: React.CSSProperties = {
    padding: '12px 14px',
    borderBottom: '1px solid #f0f0f0',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    background: 'linear-gradient(135deg, #f6f7fb 0%, #eef2ff 100%)'
  };
  const logListStyle: React.CSSProperties = {
    padding: 12,
    overflowY: 'auto',
    height: '100%',
  };
  const rowStyle: React.CSSProperties = {
    display: 'flex',
    gap: 8,
    alignItems: 'center',
    padding: '6px 8px',
    borderBottom: '1px solid #f1f1f1',
  };
  const tsStyle: React.CSSProperties = { fontFamily: 'monospace', color: '#6b7280', width: 72 };
  const siteStyle: React.CSSProperties = { fontFamily: 'monospace', color: '#374151', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const };
  const messageStyle: React.CSSProperties = { flex: 1, color: '#111' };
  const badgeStyle: React.CSSProperties = {
    padding: '2px 6px',
    borderRadius: 999,
    fontSize: 12,
    color: '#fff',
  };
  // Render
  return (
    <div style={containerStyle} aria-label="Removal log screen">
      <section style={leftStyle} aria-label="Live logs">
        <div style={headerStyle}>
          <strong>Live Logs</strong>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={togglePause} aria-label="Pause streaming" style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #ccc', background: paused ? '#ffd' : '#fff' }}>
              {paused ? 'Resume' : 'Pause'}
            </button>
            <button onClick={clearLogs} aria-label="Clear logs" style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid #ccc' }}>Clear</button>
          </div>
        </div>
        <div style={logListStyle}>
          {logs.map((l) => (
            <div key={l.id} style={rowStyle} title={l.ts}>
              <span style={tsStyle}>{l.ts}</span>
              <span style={{ ...badgeStyle, background: levelColor[l.level] }}>{l.level.toUpperCase()}</span>
              <span style={siteStyle} title={l.site ?? ''}>{l.site ?? ''}</span>
              <span style={messageStyle}>{l.message}</span>
            </div>
          ))}
          <div ref={endRef} />
        </div>
      </section>
      <section style={rightStyle} aria-label="Reasoning">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <strong>Reasoning</strong>
          <span style={{ fontSize: 12, color: '#6b7280' }}>High-level plan</span>
        </div>
        <div style={{ paddingTop: 8, paddingRight: 6, overflow: 'auto' }}>
          <div style={{ marginBottom: 6 }}><strong>Goal:</strong> {reasoning.goal}</div>
          <div style={{ marginBottom: 6 }}><strong>Approach:</strong> {reasoning.approach}</div>
          <div style={{ marginBottom: 6 }}><strong>Constraints:</strong> {reasoning.constraints.join(' • ')}</div>
          {reasoning.lastNote && <div style={{ marginTop: 8 }}><strong>Note:</strong> {reasoning.lastNote}</div>}
        </div>
      </section>
    </div>
  );
};
export default RemovalLogScreen;
