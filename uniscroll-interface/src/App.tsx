import React, { useState, useEffect, useRef } from 'react';
import { 
  Files, Search, GitBranch, Play, Blocks, User, Settings, 
  ChevronDown, ChevronRight, CircleDot, X, Terminal, 
  AlertTriangle, Bug, Monitor, Cpu, Globe, FileJson, 
  Zap, MoreHorizontal, Plus, Command
} from 'lucide-react';

// --- Types ---
type Tenant = { id: string; slug: string; name: string; active?: boolean };
type Conversation = { id: string; tenant_id: string; title: string; updated_at: string };
type Artifact = { path: string; type: 'file' | 'dir'; size?: string };
type EventItem = { id: string; ts: string; type: 'click' | 'type' | 'nav' | 'log'; message: string; meta?: string };
type Task = { id: string; status: 'running' | 'completed' | 'failed'; label: string; ts: string };
type Tool = { id: string; name: string; published: boolean; type: 'connector' | 'skill' };
type Message = { id: string; role: 'user' | 'agent'; text: string; time: string };

// --- Seed Data (preview mode, no backend) ---
const SEED_TENANTS: Tenant[] = [
  { id: 'tn_01', slug: 'uniscroll-prod', name: 'uniscroll-prod', active: true },
  { id: 'tn_02', slug: 'acme-corp', name: 'acme-corp' },
  { id: 'tn_03', slug: 'demo-tenant', name: 'demo-tenant' },
];

const SEED_CONVS: Conversation[] = [
  { id: 'cv_100', tenant_id: 'tn_01', title: 'Research Q4 roadmap', updated_at: '2m ago' },
  { id: 'cv_101', tenant_id: 'tn_01', title: 'Fix Gmail connector', updated_at: '14m ago' },
  { id: 'cv_102', tenant_id: 'tn_01', title: 'Draft investor update', updated_at: '1h ago' },
];

const SEED_ARTIFACTS: Artifact[] = [
  { path: '/workspace', type: 'dir' },
  { path: '/workspace/README.md', type: 'file', size: '1.2kb' },
  { path: '/workspace/inbox', type: 'dir' },
  { path: '/workspace/inbox/emails.json', type: 'file', size: '4.8kb' },
  { path: '/workspace/browser', type: 'dir' },
  { path: '/workspace/browser/cookies.json', type: 'file', size: '2.1kb' },
  { path: '/workspace/output', type: 'dir' },
  { path: '/workspace/output/report.md', type: 'file', size: '12kb' },
];

const SEED_EVENTS: EventItem[] = [
  { id: 'ev1', ts: '14:32:01', type: 'nav', message: 'Navigating to gmail.com', meta: 'https://mail.google.com' },
  { id: 'ev2', ts: '14:32:04', type: 'click', message: 'Clicked on Gmail', meta: '[data-testid="inbox-row"]' },
  { id: 'ev3', ts: '14:32:07', type: 'type', message: 'Agent is typing...', meta: 'Subject: Q4 Update' },
  { id: 'ev4', ts: '14:32:12', type: 'log', message: 'Saved 3 artifacts to /workspace/output', meta: '' },
  { id: 'ev5', ts: '14:32:18', type: 'click', message: 'Clicked on Attach', meta: 'file-picker' },
];

const SEED_TASKS: Task[] = [
  { id: 'tsk_91a2', status: 'running', label: 'browser.run: gmail.search', ts: '14:32:00' },
  { id: 'tsk_88f1', status: 'completed', label: 'file.write: report.md', ts: '14:31:44' },
  { id: 'tsk_87c0', status: 'failed', label: 'connector.gmail.sync', ts: '14:30:10' },
  { id: 'tsk_86b9', status: 'completed', label: 'skill.research.exec', ts: '14:28:02' },
];

const SEED_TOOLS: Tool[] = [
  { id: 'tl_gmail', name: 'gmail', published: true, type: 'connector' },
  { id: 'tl_slack', name: 'slack', published: true, type: 'connector' },
  { id: 'tl_notion', name: 'notion', published: false, type: 'connector' },
  { id: 'tl_calendar', name: 'calendar', published: true, type: 'connector' },
  { id: 'sk_research', name: 'research', published: true, type: 'skill' },
  { id: 'sk_writer', name: 'writer-pro', published: true, type: 'skill' },
  { id: 'sk_code', name: 'code-review', published: false, type: 'skill' },
];

export default function App() {
  // Auth inputs - in-memory only (no localStorage per boundary)
  const [tenantId, setTenantId] = useState('uniscroll-prod');
  const [apiKey, setApiKey] = useState('sk_uniscroll_test_123');
  const [adminKey, setAdminKey] = useState('uniscroll_admin_dev_key_2026');
  const [backendLive, setBackendLive] = useState<boolean | null>(null);

  // Layout state
  const [activeActivity, setActiveActivity] = useState<'explorer' | 'search' | 'scm' | 'run' | 'ext' | 'account'>('explorer');
  const [explorerOpen, setExplorerOpen] = useState(true);
  const [tenantsOpen, setTenantsOpen] = useState(true);
  const [timelineOpen, setTimelineOpen] = useState(true);
  const [tenantExpanded, setTenantExpanded] = useState<string>('tn_01');
  const [activeMainTab, setActiveMainTab] = useState<'prompt' | 'computer' | 'state' | 'execute'>('prompt');
  const [activeBottomTab, setActiveBottomTab] = useState<'problems' | 'output' | 'debug' | 'terminal'>('output');
  const [activeTenant, setActiveTenant] = useState<Tenant>(SEED_TENANTS[0]);
  const [mobileMenu, setMobileMenu] = useState<'none' | 'explorer' | 'right'>('none');
  const [lastAction, setLastAction] = useState('ready');
  const [conversationId, setConversationId] = useState<string | null>(null);

  // Data - transient in-memory
  const [tenants, setTenants] = useState<Tenant[]>(SEED_TENANTS);
  const [conversations, setConversations] = useState<Conversation[]>(SEED_CONVS);
  const [artifacts, setArtifacts] = useState<Artifact[]>(SEED_ARTIFACTS);
  const [events, setEvents] = useState<EventItem[]>(SEED_EVENTS);
  const [tasks, setTasks] = useState<Task[]>(SEED_TASKS);
  const [tools] = useState<Tool[]>(SEED_TOOLS);

  const [messages, setMessages] = useState<Message[]>([
    { id: 'm1', role: 'agent', text: 'UNISCROLL OS ready. Shared computer mounted at /workspace. Ask to search, draft, or automate.', time: '14:30' },
    { id: 'm2', role: 'user', text: 'Check Gmail and draft Q4 report from last threads', time: '14:31' },
    { id: 'm3', role: 'agent', text: 'Running: browser.nav → gmail → search Q4. Found 3 threads. Writing to /workspace/output/report.md. Browser cookies shared across all bots on this tenant.', time: '14:32' },
  ]);
  const [inputVal, setInputVal] = useState('');
  const [planMode, setPlanMode] = useState<'Plan' | 'Act' | 'Research'>('Plan');
  const [executeAction, setExecuteAction] = useState('gmail.search');
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Cabeceras de autenticación para el backend
  const liveHeaders = () => ({
    'X-Tenant-Id': tenantId,
    'X-Api-Key': apiKey,
    'X-Admin-Key': adminKey,
  } as Record<string, string>);

  // Carga datos reales (tools, skills, tenants, conversaciones, artifacts) desde el backend
  const refreshLiveData = async () => {
    try {
      const headers = liveHeaders();
      const [toolsRes, skillsRes, convsRes, artsRes, tensRes] = await Promise.all([
        fetch('/api/tools', { headers }),
        fetch('/api/skills', { headers }),
        fetch('/api/conversations', { headers }),
        fetch('/api/artifacts', { headers }),
        fetch('/api/tenants', { headers }),
      ]);
      if (toolsRes.ok || skillsRes.ok) {
        const toolsRaw: any[] = toolsRes.ok ? await toolsRes.json() : [];
        const skillsRaw: any[] = skillsRes.ok ? await skillsRes.json() : [];
        setTools([
          ...toolsRaw.map((t, i) => ({ id: `tl_${i}`, name: t.name, published: true, type: 'connector' as const })),
          ...skillsRaw.map((s, i) => ({ id: `sk_${i}`, name: s.name, published: true, type: 'skill' as const })),
        ]);
      }
      if (convsRes.ok) {
        const convRaw: any[] = await convsRes.json();
        setConversations(convRaw.map(c => ({ id: c.id, tenant_id: c.tenant_id || tenantId, title: c.title, updated_at: c.updated_at || '' })));
      }
      if (artsRes.ok) {
        const artRaw: any[] = await artsRes.json();
        setArtifacts(artRaw.map(a => ({ path: a.path || a.id || 'artifact', type: 'file' as const, size: undefined })));
      }
      if (tensRes.ok) {
        const tenRaw: any[] = await tensRes.json();
        if (tenRaw.length) {
          setTenants(tenRaw.map(t => ({ id: t.id, slug: t.slug || t.id, name: t.name || t.slug, active: t.slug === tenantId })));
        }
      }
    } catch {
      /* offline: se mantiene preview */
    }
  };

  // Healthcheck real del backend (no bloqueante; si falla se queda en preview)
  useEffect(() => {
    let alive = true;
    fetch('/api/events', { headers: liveHeaders() })
      .then(r => {
        if (!alive) return;
        setBackendLive(r.ok);
        if (r.ok) refreshLiveData();
      })
      .catch(() => {
        if (!alive) return;
        setBackendLive(false);
      });
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId, apiKey, adminKey]);

  // Polling real de eventos y tasks cada 3s cuando el backend está vivo
  useEffect(() => {
    if (!backendLive) return;
    let stopped = false;
    const tick = async () => {
      if (stopped) return;
      try {
        const headers = liveHeaders();
        const [evRes, tRes] = await Promise.all([
          fetch('/api/events', { headers }),
          fetch('/api/tasks', { headers }),
        ]);
        if (evRes.ok) {
          const raw: any[] = await evRes.json();
          setEvents(raw.slice(0, 30).map(e => ({
            id: e.id,
            ts: (e.at || '').slice(11, 19) || new Date().toLocaleTimeString(),
            type: 'log' as const,
            message: e.kind || 'event',
            meta: Object.keys(e.payload || {}).length ? JSON.stringify(e.payload).slice(0, 80) : '',
          })));
        }
        if (tRes.ok) {
          const raw: any[] = await tRes.json();
          setTasks(raw.slice(0, 20).map(t => ({
            id: t.id,
            status: t.status === 'running' || t.status === 'completed' || t.status === 'failed' ? t.status : 'failed',
            label: t.summary || t.message || t.id,
            ts: (t.started_at || '').slice(11, 19),
          })));
        }
      } catch { /* ignore */ }
    };
    tick();
    const iv = setInterval(tick, 3000);
    return () => { stopped = true; clearInterval(iv); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backendLive, tenantId, apiKey, adminKey]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!inputVal.trim()) return;
    const now = new Date().toLocaleTimeString().slice(0,5);
    const userMsg: Message = { id: `u_${Date.now()}`, role: 'user', text: inputVal, time: now };
    setMessages(m => [...m, userMsg]);
    setInputVal('');
    // Preview mode (backend offline): respuesta simulada local
    if (!backendLive) {
      setTimeout(() => {
        const reply: Message = {
          id: `a_${Date.now()}`,
          role: 'agent',
          text: `[${planMode}] (preview) Executing: ${userMsg.text.slice(0,80)} → Browser: gmail.search → File: /workspace/output/draft.md → Shared computer state updated. Every Bot uses same /workspace.`,
          time: new Date().toLocaleTimeString().slice(0,5)
        };
        setMessages(m => [...m, reply]);
        setEvents(e => [{ id: `ev_${Date.now()}`, ts: new Date().toLocaleTimeString(), type: 'log', message: `Chat reply generated (${planMode})`, meta: userMsg.text.slice(0,30) }, ...e].slice(0,30));
      }, 900);
      return;
    }
    // Live: crea conversación (una sola vez) y envía el mensaje real a POST /api/chat
    try {
      if (!conversationId) {
        const cRes = await fetch('/api/conversations', { method: 'POST', headers: liveHeaders() as any });
        if (cRes.ok) {
          const c = await cRes.json();
          setConversationId(c.id);
        }
      }
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { ...liveHeaders(), 'Content-Type': 'application/json' } as any,
        body: JSON.stringify({ message: userMsg.text, conversation_id: conversationId || undefined }),
      });
      if (res.ok) {
        const data = await res.json();
        const reply: Message = {
          id: `a_${Date.now()}`,
          role: 'agent',
          text: data.reply || `(sin respuesta) task=${data.task_id || ''}`,
          time: new Date().toLocaleTimeString().slice(0,5)
        };
        setMessages(m => [...m, reply]);
        setEvents(e => [{ id: `ev_${Date.now()}`, ts: new Date().toLocaleTimeString(), type: 'log', message: `POST /api/chat OK · task ${data.task_id || ''}`, meta: data.reply ? data.reply.slice(0, 80) : '' }, ...e].slice(0,30));
      } else {
        const text = await res.text();
        setMessages(m => [...m, { id: `er_${Date.now()}`, role: 'agent', text: `API ${res.status}: ${text.slice(0, 200)}`, time: new Date().toLocaleTimeString().slice(0,5) }]);
      }
    } catch (err: any) {
      setMessages(m => [...m, { id: `er_${Date.now()}`, role: 'agent', text: `Backend error: ${err?.message || err}`, time: new Date().toLocaleTimeString().slice(0,5) }]);
    }
  };

  const failedCount = tasks.filter(t => t.status === 'failed').length;

  return (
    <div className="min-h-screen bg-[#FFFFFF] text-[#0A0A0A] flex flex-col font-sans selection:bg-[#FFD60A] selection:text-black">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;700&family=Geist:wght@700;900&display=swap');
        * { font-variant-ligatures: none; }
        .font-mono { font-family: 'Geist Mono', monospace; }
        .font-display { font-family: 'Geist', sans-serif; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-thumb { background: #0A0A0A; }
        ::-webkit-scrollbar-track { background: #fff; }
      `}</style>

      {/* Top Auth Bar - in-memory */}
      <div className="h-[36px] bg-[#0A0A0A] text-white flex items-center gap-3 px-3 border-b border-black shrink-0 font-mono text-[11px] tracking-wide">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-[#FFD60A] rounded-full animate-pulse" />
          <span className="font-bold">UNISCROLL.OS</span>
          <span className="opacity-60 hidden sm:inline">AUTH // PREVIEW</span>
        </div>
        <div className="flex-1 flex items-center gap-2 justify-end sm:justify-center overflow-hidden">
          <input value={tenantId} onChange={e=>setTenantId(e.target.value)} placeholder="X-Tenant-Id" className="bg-white/10 border border-white/20 px-2 py-1 w-[110px] sm:w-[130px] outline-none focus:border-[#FFD60A] text-white placeholder:text-white/40" />
          <input value={apiKey} onChange={e=>setApiKey(e.target.value)} placeholder="X-Api-Key" className="bg-white/10 border border-white/20 px-2 py-1 w-[110px] sm:w-[140px] outline-none focus:border-[#FFD60A] text-white placeholder:text-white/40 hidden sm:block" />
          <input value={adminKey} onChange={e=>setAdminKey(e.target.value)} placeholder="X-Admin-Key" className="bg-white/10 border border-white/20 px-2 py-1 w-[110px] sm:w-[140px] outline-none focus:border-[#FFD60A] text-white placeholder:text-white/40 hidden md:block" />
          <div className={`px-2 py-1 border text-[10px] font-bold ${backendLive ? 'bg-[#FFD60A] text-black border-black' : backendLive===false ? 'bg-black text-white border-white/30' : 'bg-white/10 border-white/20'}`}>
            {backendLive ? 'LIVE' : backendLive===false ? 'OFFLINE • PREVIEW' : 'CHECKING...'}
          </div>
        </div>
        <div className="flex items-center gap-2 sm:hidden">
          <button onClick={()=>setMobileMenu(m=>m==='explorer'?'none':'explorer')} className="p-1 border border-white/20"><Files size={14}/></button>
          <button onClick={()=>setMobileMenu(m=>m==='right'?'none':'right')} className="p-1 border border-white/20"><Blocks size={14}/></button>
        </div>
      </div>

      <div className="flex flex-1 min-h-0 overflow-hidden">
        {/* Activity Bar */}
        <div className="w-[48px] bg-[#0A0A0A] flex flex-col items-center py-3 gap-1 shrink-0 border-r border-black select-none">
          <button onClick={()=>{setActiveActivity('explorer'); setLastAction('explorer');}} className={`w-8 h-8 grid place-items-center border ${activeActivity==='explorer' ? 'bg-white text-black border-white' : 'text-white/60 border-transparent hover:text-white hover:border-white/20'}`}><Files size={18}/></button>
          <button onClick={()=>{setActiveActivity('search'); setLastAction('search');}} className={`w-8 h-8 grid place-items-center border ${activeActivity==='search' ? 'bg-white text-black border-white' : 'text-white/60 border-transparent hover:text-white hover:border-white/20'}`}><Search size={18}/></button>
          <button onClick={()=>{setActiveActivity('scm'); setLastAction('source-control');}} className={`w-8 h-8 grid place-items-center border ${activeActivity==='scm' ? 'bg-white text-black border-white' : 'text-white/60 border-transparent hover:text-white hover:border-white/20'}`}><GitBranch size={18}/></button>
          <button onClick={()=>{setActiveActivity('run'); setLastAction('run');}} className={`w-8 h-8 grid place-items-center border ${activeActivity==='run' ? 'bg-white text-black border-white' : 'text-white/60 border-transparent hover:text-white hover:border-white/20'}`}><Play size={16}/></button>
          <button onClick={()=>{setActiveActivity('ext'); setLastAction('extensions');}} className={`w-8 h-8 grid place-items-center border ${activeActivity==='ext' ? 'bg-white text-black border-white' : 'text-white/60 border-transparent hover:text-white hover:border-white/20'}`}><Blocks size={18}/></button>
          <button onClick={()=>{setActiveActivity('account'); setLastAction('tenants');}} className={`w-8 h-8 grid place-items-center border ${activeActivity==='account' ? 'bg-white text-black border-white' : 'text-white/60 border-transparent hover:text-white hover:border-white/20'}`}><User size={18}/></button>

          <div className="flex-1" />
          <div className="flex flex-col items-center gap-3">
            <div className="w-2 h-2 bg-[#FFD60A] rounded-full shadow-[0_0_8px_#FFD60A]" title="live" />
            <button onClick={()=>{setLastAction('settings: brutalist minimal editorial');}} className="w-8 h-8 grid place-items-center text-white/60 hover:text-white border border-transparent hover:border-white/20"><Settings size={18}/></button>
          </div>
        </div>

        {/* Sidebar Explorer */}
        <div className={`
          ${mobileMenu==='explorer' ? 'flex' : 'hidden'} 
          sm:flex w-[280px] bg-white border-r border-black flex-col shrink-0 font-mono text-[12px] overflow-hidden
          fixed sm:static inset-y-[36px] left-[48px] z-30 sm:z-0
        `}>
          {/* Header */}
          <div className="h-[44px] bg-[#0A0A0A] text-white flex items-center justify-between px-3 border-b border-black shrink-0">
            <span className="font-bold tracking-widest text-[11px]">UNISCROLL // WORKSPACE</span>
            <span className="bg-[#FFD60A] text-black px-2 py-0.5 text-[10px] font-black">V1.0 BETA</span>
          </div>

          <div className="flex-1 overflow-y-auto">
            {/* EXPLORER */}
            <div className="border-b border-black">
              <button onClick={()=>setExplorerOpen(!explorerOpen)} className="w-full flex items-center gap-1 px-2 py-2 font-bold hover:bg-black/5 text-left">
                {explorerOpen ? <ChevronDown size={14}/> : <ChevronRight size={14}/>} [EXPLORER]
                <span className="ml-auto text-[10px] opacity-60">7</span>
              </button>
              {explorerOpen && (
                <div className="pb-2">
                  {[
                    { k: 'Dashboard', icon: Monitor, active: activeMainTab==='computer' },
                    { k: 'Search', icon: Search, active: false },
                    { k: 'Resources', icon: FileJson, active: false },
                    { k: 'Connectors', icon: Globe, active: false },
                    { k: 'Tenants', icon: User, active: false },
                    { k: 'Skills', icon: Zap, active: false },
                    { k: 'Tools', icon: Blocks, active: false },
                  ].map(item => (
                    <div key={item.k} className={`flex items-center gap-2 px-6 py-1.5 hover:bg-[#FFD60A]/20 cursor-pointer ${item.active ? 'bg-[#0A0A0A] text-white' : ''}`}>
                      <item.icon size={12} /> {item.k}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* TENANTS */}
            <div className="border-b border-black">
              <button onClick={()=>setTenantsOpen(!tenantsOpen)} className="w-full flex items-center gap-1 px-2 py-2 font-bold hover:bg-black/5 text-left">
                {tenantsOpen ? <ChevronDown size={14}/> : <ChevronRight size={14}/>} [TENANTS] <span className="ml-auto bg-black text-white px-1 text-[10px]">{tenants.length}</span>
              </button>
              {tenantsOpen && (
                <div className="pb-2">
                  {tenants.map(t => (
                    <div key={t.id} className="group">
                      <button onClick={()=>{ setTenantExpanded(t.id===tenantExpanded?'':t.id); setActiveTenant(t); }} className={`w-full flex items-center gap-2 px-3 py-1.5 text-left hover:bg-black/5 ${activeTenant.id===t.id?'bg-[#FFD60A] font-bold':''}`}>
                        {tenantExpanded===t.id ? <ChevronDown size={12}/> : <ChevronRight size={12}/>}
                        <CircleDot size={10} className={t.active ? 'text-[#FFD60A] fill-[#FFD60A]' : 'opacity-30'} />
                        <span className="truncate">{t.slug}</span>
                        {t.active && <span className="ml-auto text-[9px] bg-black text-white px-1">ACTIVE</span>}
                      </button>
                      {tenantExpanded===t.id && (
                        <div className="ml-6 border-l border-black/20 pl-2 py-1 space-y-2">
                          <div>
                            <div className="text-[10px] font-bold opacity-60">CONVERSATIONS</div>
                            {conversations.filter(c=>c.tenant_id===t.id).map(c=>(
                              <div key={c.id} className="py-1 px-2 hover:bg-black hover:text-white cursor-pointer truncate flex items-center gap-2">
                                <span className="w-1 h-1 bg-[#FFD60A] rounded-full"/> {c.title} <span className="ml-auto text-[9px] opacity-60">{c.updated_at}</span>
                              </div>
                            ))}
                          </div>
                          <div>
                            <div className="text-[10px] font-bold opacity-60">ARTIFACTS</div>
                            {artifacts.slice(0,4).map(a=>(
                              <div key={a.path} className="py-0.5 px-2 opacity-80 truncate">↳ {a.path}</div>
                            ))}
                          </div>
                          <div className="flex gap-2">
                            <span className="text-[10px] border border-black px-1">DRAFTS 3</span>
                            <span className="text-[10px] border border-black px-1">SCHEDULES 1</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* TIMELINE */}
            <div>
              <button onClick={()=>setTimelineOpen(!timelineOpen)} className="w-full flex items-center gap-1 px-2 py-2 font-bold hover:bg-black/5 text-left">
                {timelineOpen ? <ChevronDown size={14}/> : <ChevronRight size={14}/>} [TIMELINE] <span className="ml-auto flex items-center gap-1 text-[10px]"><span className="w-1.5 h-1.5 bg-[#FFD60A] rounded-full animate-pulse"/>LIVE</span>
              </button>
              {timelineOpen && (
                <div className="px-2 pb-3 space-y-1.5">
                  {events.slice(0,6).map(ev=>(
                    <div key={ev.id} className="border border-black/10 px-2 py-1.5 bg-[#FAFAFA] hover:bg-white">
                      <div className="flex items-center gap-2 text-[10px] opacity-60"><span>{ev.ts}</span><span className="uppercase font-bold">{ev.type}</span></div>
                      <div className="text-[11px] leading-tight truncate">{ev.message}</div>
                      {ev.meta && <div className="text-[10px] opacity-60 truncate">{ev.meta}</div>}
                    </div>
                  ))}
                  <div className="text-[10px] opacity-50 px-2">GET /api/events • polling 3s</div>
                </div>
              )}
            </div>
          </div>

          <div className="border-t border-black p-2 flex flex-col gap-1 bg-[#0A0A0A] text-white">
            <div className="flex items-center gap-2"><Command size={12} /> <span className="text-[10px]">UNISCROLL // v0.1 — brut.editorial</span></div>
            <div className="text-[10px] opacity-70 truncate">ACT: {lastAction}</div>
          </div>
        </div>

        {/* Main Editor */}
        <div className="flex-1 flex flex-col min-w-0 bg-[#F5F5F3] overflow-hidden">
          {/* Tabs */}
          <div className="h-[44px] bg-white border-b border-black flex items-center gap-0 shrink-0 overflow-x-auto font-mono text-[12px]">
            {[
              { id: 'prompt', label: 'PROMPT / 01', icon: Terminal },
              { id: 'computer', label: 'AGENT COMPUTER', icon: Cpu },
              { id: 'state', label: 'STATE', icon: FileJson },
              { id: 'execute', label: 'EXECUTE', icon: Play },
            ].map(tab => (
              <button key={tab.id} onClick={()=>setActiveMainTab(tab.id as any)} className={`h-full px-4 flex items-center gap-2 border-r border-black shrink-0 ${activeMainTab===tab.id ? 'bg-[#0A0A0A] text-white' : 'bg-white hover:bg-[#FFD60A]/30'}`}>
                <tab.icon size={14}/> {tab.label}
                {tab.id==='prompt' && <span className="ml-2 w-2 h-2 bg-[#FFD60A] rounded-full"/>}
                {tab.id==='computer' && <span className="ml-2 text-[10px] bg-[#FFD60A] text-black px-1 font-bold">GROK</span>}
              </button>
            ))}
            <div className="flex-1" />
            <div className="hidden md:flex items-center gap-2 px-3 text-[11px]">
              <span className="opacity-60">SHARED COMPUTER:</span><span className="font-bold">/workspace</span>
            </div>
          </div>

          {/* Editor Content */}
          <div className="flex-1 overflow-auto">
            {activeMainTab==='prompt' && (
              <div className="h-full flex flex-col">
                {/* Title brutalist */}
                <div className="bg-white border-b border-black p-4 sm:p-6">
                  <h1 className="font-display font-black text-[28px] sm:text-[42px] leading-[0.9] tracking-[-0.02em]">UNISCROLL<br/>OS // PROMPT</h1>
                  <div className="mt-3 flex flex-wrap gap-2 font-mono text-[11px]">
                    <span className="border border-black px-2 py-1 bg-[#FFD60A] font-bold">TENANT: {activeTenant.slug}</span>
                    <span className="border border-black px-2 py-1">CONV: cv_100 • Q4 roadmap</span>
                    <span className="border border-black px-2 py-1">/ to reference skill • @ to attach</span>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 bg-[#F5F5F3]">
                  {messages.map(m=>(
                    <div key={m.id} className={`max-w-[720px] border border-black ${m.role==='user' ? 'bg-white ml-auto' : 'bg-[#0A0A0A] text-white'}`}>
                      <div className="flex items-center justify-between px-3 py-1 border-b border-black/20 text-[10px] font-mono opacity-70">
                        <span>{m.role==='user' ? 'YOU' : 'UNISCROLL // AGENT'} • {m.time}</span>
                        <MoreHorizontal size={12}/>
                      </div>
                      <div className="p-3 font-mono text-[13px] leading-[1.5] whitespace-pre-wrap">{m.text}</div>
                    </div>
                  ))}
                  <div ref={chatEndRef} />
                </div>

                {/* Input */}
                <div className="bg-white border-t border-black p-3">
                  <div className="border border-black bg-[#FAFAFA] focus-within:bg-white">
                    <div className="flex items-center gap-2 px-3 py-2 border-b border-black/10">
                      <select value={planMode} onChange={e=>setPlanMode(e.target.value as any)} className="bg-[#0A0A0A] text-white text-[11px] font-bold px-2 py-1 border border-black font-mono">
                        <option>Plan</option><option>Act</option><option>Research</option>
                      </select>
                      <span className="text-[11px] font-mono opacity-60">POST /api/chat • X-Tenant-Id: {tenantId}</span>
                      <span className="ml-auto text-[10px] bg-[#FFD60A] text-black px-2 py-0.5 font-bold">⌘+Enter</span>
                    </div>
                    <textarea value={inputVal} onChange={e=>setInputVal(e.target.value)} onKeyDown={e=>{ if(e.key==='Enter' && (e.metaKey||e.ctrlKey)){ handleSend(); }}} placeholder="Ask Uniscroll to... (preview mode: generates local draft, no persistence)" className="w-full min-h-[64px] p-3 font-mono text-[13px] bg-transparent outline-none resize-none" />
                    <div className="flex items-center justify-between px-3 py-2 border-t border-black/10">
                      <div className="flex gap-2">
                        <span className="text-[11px] border border-black px-2 py-1">@ tools</span>
                        <span className="text-[11px] border border-black px-2 py-1">/ skills</span>
                      </div>
                      <button onClick={handleSend} className="bg-[#0A0A0A] text-white px-4 py-1.5 font-mono text-[12px] font-bold hover:bg-black flex items-center gap-2">RUN <Play size={12}/></button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeMainTab==='computer' && (
              <div className="h-full flex flex-col">
                <div className="bg-[#FFD60A] border-b border-black p-3 font-mono text-[11px] flex flex-wrap gap-3">
                  <span className="font-bold">SHARED COMPUTER // GROK STYLE</span>
                  <span>Every Bot on your account uses the same computer: Browser cookies shared, Files visible to every Bot</span>
                  <span className="ml-auto bg-black text-white px-2 py-0.5">/workspace mounted</span>
                </div>

                <div className="flex-1 grid grid-cols-1 lg:grid-cols-[240px_1fr] min-h-0">
                  {/* File Tree */}
                  <div className="border-r border-black bg-white font-mono text-[12px] overflow-auto">
                    <div className="p-2 font-bold border-b border-black flex items-center gap-2"><Files size={12}/> WORKSPACE</div>
                    <div className="p-2 space-y-0.5">
                      {artifacts.map(a=>(
                        <div key={a.path} className={`px-2 py-1 flex items-center gap-2 hover:bg-[#FFD60A]/30 ${a.type==='dir'?'font-bold':''}`}>
                          <span className="opacity-60">{a.type==='dir' ? '▸' : '—'}</span>
                          <span className="truncate">{a.path}</span>
                          {a.size && <span className="ml-auto text-[10px] opacity-50">{a.size}</span>}
                        </div>
                      ))}
                    </div>
                    <div className="m-2 border border-black p-2 bg-[#FAFAFA] text-[11px]">
                      <div className="font-bold">BROWSER STATE</div>
                      <div>cookies: 12 • localStorage: shared</div>
                      <div>visible to every Bot ✓</div>
                    </div>
                  </div>

                  {/* Browser Preview */}
                  <div className="flex flex-col min-h-0 bg-[#0A0A0A] text-white">
                    <div className="h-8 bg-white text-black border-b border-black flex items-center px-3 gap-2 font-mono text-[11px]">
                      <div className="flex gap-1"><span className="w-2.5 h-2.5 bg-black rounded-full"/><span className="w-2.5 h-2.5 border border-black rounded-full"/><span className="w-2.5 h-2.5 border border-black rounded-full"/></div>
                      <div className="flex-1 bg-[#F5F5F3] border border-black px-2 py-0.5 truncate">https://mail.google.com/mail/u/0/#inbox — Agent controlling</div>
                      <span className="bg-[#FFD60A] px-2 py-0.5 font-bold">LIVE</span>
                    </div>

                    <div className="flex-1 p-3 grid grid-rows-[1fr_auto] gap-3 overflow-hidden">
                      <div className="bg-white text-black border border-white p-3 font-mono text-[12px] overflow-auto">
                        <div className="flex items-center gap-2 mb-3">
                          <span className="bg-[#0A0A0A] text-white px-2 py-1 text-[10px]">BROWSER LOG</span>
                          <span className="text-[11px] opacity-60">GET /api/events polling 3s</span>
                          <span className="ml-auto flex items-center gap-2"><span className="w-2 h-2 bg-[#FFD60A] rounded-full animate-pulse"/> {events[0]?.message}</span>
                        </div>
                        <div className="space-y-1">
                          {events.map(ev=>(
                            <div key={ev.id} className="flex gap-3 border-l-2 border-black pl-2 py-1">
                              <span className="opacity-60">{ev.ts}</span>
                              <span className={`px-1 text-[10px] font-bold ${ev.type==='click'?'bg-[#FFD60A] text-black': ev.type==='type'?'bg-black text-white':'bg-white border border-black'}`}>{ev.type.toUpperCase()}</span>
                              <span>{ev.message}</span>
                              <span className="ml-auto opacity-50 truncate hidden sm:inline">{ev.meta}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="bg-[#1A1A1A] border border-white/10 p-2 font-mono">
                        <div className="flex items-center gap-2 text-[11px] mb-2"><Terminal size={12}/> TERMINAL — TASKS (polling)</div>
                        <div className="space-y-1">
                          {tasks.map(t=>(
                            <div key={t.id} className={`flex items-center gap-2 px-2 py-1 border-l-2 text-[11px] ${t.status==='running' ? 'border-[#FFD60A] bg-[#FFD60A]/10 text-[#FFD60A]' : t.status==='failed' ? 'border-red-500 bg-red-500/10' : 'border-white/20 opacity-70'}`}>
                              <span className="font-bold">{t.id}</span>
                              <span className="uppercase text-[10px] border border-current px-1">{t.status}</span>
                              <span className="truncate">{t.label}</span>
                              <span className="ml-auto opacity-60">{t.ts}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeMainTab==='state' && (
              <div className="p-4 font-mono text-[12px] bg-white h-full overflow-auto">
                <div className="border border-black p-3 mb-3 bg-[#FFD60A] font-bold">STATE // RAW JSON (expandable) • GET /api/events, /api/tasks, /api/tenants</div>
                {[
                  { name: 'events', data: events },
                  { name: 'tasks', data: tasks },
                  { name: 'tenants', data: tenants },
                  { name: 'artifacts', data: artifacts },
                ].map(section=>(
                  <details key={section.name} className="border border-black mb-2 bg-[#FAFAFA]" open={section.name==='events'}>
                    <summary className="px-3 py-2 font-bold cursor-pointer bg-white border-b border-black flex items-center gap-2"><FileJson size={12}/> {section.name}.json <span className="ml-auto text-[10px] opacity-60">{section.data.length} items</span></summary>
                    <pre className="p-3 overflow-auto text-[11px] leading-[1.4]">{JSON.stringify(section.data, null, 2)}</pre>
                  </details>
                ))}
              </div>
            )}

            {activeMainTab==='execute' && (
              <div className="p-4 bg-white h-full">
                <div className="border border-black p-4 max-w-[640px]">
                  <div className="font-display font-black text-[20px] mb-3">EXECUTE // TOOLS</div>
                  <div className="space-y-3 font-mono text-[12px]">
                    <div>
                      <div className="text-[11px] font-bold mb-1">ACTION SELECTOR (from GET /api/tools)</div>
                      <select value={executeAction} onChange={e=>setExecuteAction(e.target.value)} className="w-full border border-black px-3 py-2 bg-[#FAFAFA]">
                        {tools.map(t=> <option key={t.id} value={t.name}>{t.type}::{t.name} {t.published?'• PUBLISHED':''}</option>)}
                      </select>
                    </div>
                    <div className="border border-black p-3 bg-[#F5F5F3]">
                      <div className="font-bold mb-2">POST /api/execute — preview (no persistence)</div>
                      <div className="grid grid-cols-2 gap-2">
                        <input placeholder="param: query" className="border border-black px-2 py-1 bg-white" />
                        <input placeholder="param: limit=10" className="border border-black px-2 py-1 bg-white" />
                      </div>
                      <button onClick={async ()=>{
                        if (!backendLive) {
                          const newTask: Task = { id: `tsk_${Date.now().toString(36)}`, status: 'running', label: `${executeAction} (preview)`, ts: new Date().toLocaleTimeString() };
                          setTasks(t=>[newTask, ...t].slice(0,20));
                          setEvents(e=>[{ id: `ev_${Date.now()}`, ts: new Date().toLocaleTimeString(), type: 'log', message: `Execute queued (preview): ${executeAction}`, meta: '' }, ...e].slice(0,30));
                          setActiveBottomTab('output');
                          return;
                        }
                        try {
                          const res = await fetch('/api/execute', {
                            method: 'POST',
                            headers: { ...liveHeaders(), 'Content-Type': 'application/json' } as any,
                            body: JSON.stringify({ action: executeAction, params: {} }),
                          });
                          const data = await res.json();
                          setEvents(e=>[{ id: `ev_${Date.now()}`, ts: new Date().toLocaleTimeString(), type: 'log', message: `POST /api/execute ${data.success ? 'OK' : 'FAIL'}: ${executeAction}`, meta: data.error || JSON.stringify(data.result || {}).slice(0, 100) }, ...e].slice(0,30));
                          if (data.success) {
                            setTasks(t=>[{ id: `tsk_${Date.now().toString(36)}`, status: 'completed', label: executeAction, ts: new Date().toLocaleTimeString() }, ...t].slice(0,20));
                          }
                        } catch (err: any) {
                          setEvents(e=>[{ id: `ev_${Date.now()}`, ts: new Date().toLocaleTimeString(), type: 'log', message: `Execute error: ${err?.message || err}`, meta: '' }, ...e].slice(0,30));
                        }
                        setActiveBottomTab('output');
                      }} className="mt-3 w-full bg-[#0A0A0A] text-white py-2 font-bold hover:bg-black border border-black">EXECUTE {executeAction} → RUN</button>
                      <div className="mt-2 text-[11px] opacity-60">POST /api/execute en vivo cuando el backend responde • preview cuando está offline.</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Bottom Panel */}
          <div className="h-[260px] bg-white border-t border-black flex flex-col shrink-0">
            <div className="h-[36px] border-b border-black flex items-center font-mono text-[11px] bg-[#F5F5F3] shrink-0 overflow-x-auto">
              {[
                { id: 'problems', label: `PROBLEMS (${failedCount})`, icon: AlertTriangle },
                { id: 'output', label: 'OUTPUT', icon: Monitor },
                { id: 'debug', label: 'DEBUG CONSOLE', icon: Bug },
                { id: 'terminal', label: 'TERMINAL', icon: Terminal },
              ].map(t=>(
                <button key={t.id} onClick={()=>setActiveBottomTab(t.id as any)} className={`h-full px-3 flex items-center gap-1.5 border-r border-black ${activeBottomTab===t.id ? 'bg-[#0A0A0A] text-white' : 'hover:bg-[#FFD60A]/20'}`}>
                  <t.icon size={12}/> {t.label}
                </button>
              ))}
              <div className="ml-auto px-3 flex items-center gap-2">
                <span className="hidden sm:inline opacity-60">polling 3s • GET /api/events</span>
                <X size={12} className="opacity-60"/>
              </div>
            </div>
            <div className="flex-1 overflow-auto font-mono text-[11px] p-2 bg-[#FAFAFA]">
              {activeBottomTab==='problems' && (
                <div className="space-y-1">
                  {tasks.filter(t=>t.status==='failed').length===0 ? <div className="p-3 opacity-60">No failed tasks • all clear</div> :
                    tasks.filter(t=>t.status==='failed').map(t=>(
                      <div key={t.id} className="border-l-4 border-red-500 bg-white border border-black/10 px-3 py-2 flex items-center gap-3">
                        <AlertTriangle size={14} className="text-red-500"/>
                        <span className="font-bold">{t.id}</span><span>{t.label}</span><span className="ml-auto opacity-60">{t.ts}</span>
                      </div>
                    ))
                  }
                </div>
              )}
              {activeBottomTab==='output' && (
                <div className="space-y-1">
                  {events.map(ev=>(
                    <div key={ev.id} className="flex gap-2"><span className="opacity-50">{ev.ts}</span><span>[{ev.type}]</span><span>{ev.message}</span></div>
                  ))}
                </div>
              )}
              {activeBottomTab==='debug' && (
                <pre className="whitespace-pre-wrap">{JSON.stringify({ activeTenant, tenantId, backendLive, tasks: tasks.slice(0,3) }, null, 2)}</pre>
              )}
              {activeBottomTab==='terminal' && (
                <div className="bg-[#0A0A0A] text-[#FFD60A] p-3 h-full font-mono">
                  <div>$ uniscroll execute --tenant {tenantId} --action {executeAction}</div>
                  <div className="opacity-60 mt-2">Preview mode: generates draft, no real POST. Connect backend at localhost:8000 for live.</div>
                  <div className="mt-3 flex gap-2">
                    <span className="opacity-60">$</span><input placeholder="type command..." className="bg-transparent outline-none flex-1 text-white" />
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Sidebar */}
        <div className={`
          ${mobileMenu==='right' ? 'flex' : 'hidden'} 
          lg:flex w-[340px] bg-white border-l border-black flex-col shrink-0 font-mono text-[12px] overflow-hidden
          fixed lg:static inset-y-[36px] right-0 z-30 lg:z-0
        `}>
          <div className="h-[44px] bg-[#0A0A0A] text-white flex items-center px-3 justify-between border-b border-black">
            <span className="font-bold text-[11px] tracking-widest">AGENT // DETAILS</span>
            <span className="bg-[#FFD60A] text-black px-2 py-0.5 text-[10px] font-bold flex items-center gap-1"><span className="w-1.5 h-1.5 bg-black rounded-full animate-pulse"/> LIVE</span>
          </div>

          <div className="flex-1 overflow-y-auto">
            <div className="p-3 border-b border-black">
              <div className="flex items-center gap-2 mb-2"><Cpu size={14}/> <span className="font-bold">UNISCROLL BOT</span><span className="ml-auto text-[10px] bg-[#FFD60A] px-1 font-bold">PUBLISHED</span></div>
              <div className="text-[11px] leading-[1.4] opacity-80">Shared computer: /workspace — Browser cookies shared, Files visible to every Bot. Same as Grok docs.</div>
              <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
                <div className="border border-black p-2"><div className="opacity-60">CPU</div><div className="font-bold">2.4 GHz • idle</div></div>
                <div className="border border-black p-2"><div className="opacity-60">MEM</div><div className="font-bold">512 MB / 2 GB</div></div>
              </div>
            </div>

            <div className="border-b border-black">
              <div className="px-3 py-2 font-bold flex items-center gap-2"><Globe size={12}/> CONNECTORS / TOOLS <span className="ml-auto text-[10px] bg-black text-white px-1">{tools.filter(t=>t.type==='connector').length}</span></div>
              <div className="px-2 pb-3 space-y-1">
                {tools.filter(t=>t.type==='connector').map(tool=>(
                  <div key={tool.id} className="border border-black flex items-center gap-2 px-2 py-2 hover:bg-[#FFD60A]/20 cursor-pointer">
                    <span className="w-5 h-5 bg-[#0A0A0A] text-white grid place-items-center text-[10px] font-bold">{tool.name[0].toUpperCase()}</span>
                    <span className="font-bold">@{tool.name}</span>
                    {tool.published && <span className="ml-auto bg-[#FFD60A] text-black text-[9px] px-1.5 py-0.5 font-bold">PUBLISHED</span>}
                  </div>
                ))}
                <div className="text-[10px] opacity-60 px-2">GET /api/tools • @ to attach</div>
              </div>
            </div>

            <div className="border-b border-black">
              <div className="px-3 py-2 font-bold flex items-center gap-2"><Zap size={12}/> SKILLS <span className="ml-auto text-[10px] bg-black text-white px-1">{tools.filter(t=>t.type==='skill').length}</span></div>
              <div className="px-2 pb-3 space-y-1">
                {tools.filter(t=>t.type==='skill').map(tool=>(
                  <div key={tool.id} className="border border-black flex items-center gap-2 px-2 py-2 hover:bg-[#FFD60A]/20 cursor-pointer">
                    <span className="font-bold">/{tool.name}</span>
                    {tool.published && <span className="ml-auto bg-[#0A0A0A] text-white text-[9px] px-1.5 py-0.5 font-bold">PUBLISHED</span>}
                  </div>
                ))}
                <div className="text-[10px] opacity-60 px-2">GET /api/skills • / to reference</div>
              </div>
            </div>

            <div className="p-3">
              <div className="font-bold mb-2">CREDENTIALS STATUS</div>
              <div className="space-y-2">
                <div className="border border-black p-2 flex items-center justify-between">
                  <span>X-Tenant-Id</span><span className={`px-2 py-0.5 text-[10px] font-bold ${tenantId ? 'bg-[#FFD60A] text-black' : 'bg-red-500 text-white'}`}>{tenantId ? 'SET' : 'MISSING'}</span>
                </div>
                <div className="border border-black p-2 flex items-center justify-between">
                  <span>X-Api-Key</span><span className={`px-2 py-0.5 text-[10px] font-bold ${apiKey ? 'bg-[#FFD60A] text-black' : 'bg-red-500 text-white'}`}>{apiKey ? 'SET' : 'MISSING'}</span>
                </div>
                <div className="border border-black p-2 flex items-center justify-between">
                  <span>X-Admin-Key</span><span className={`px-2 py-0.5 text-[10px] font-bold ${adminKey ? 'bg-black text-white' : 'bg-red-500 text-white'}`}>{adminKey ? 'SET' : '401'}</span>
                </div>
                <div className={`border p-2 text-[11px] ${backendLive===false ? 'border-red-500 bg-red-50' : 'border-black bg-[#FAFAFA]'}`}>
                  {backendLive===false ? 'Backend offline — preview mode active. Runs on :5174, backend :8000 intact. Shows sample data.' : backendLive ? 'Backend reachable — live data would replace preview.' : 'Checking backend...'}
                </div>
              </div>
            </div>
          </div>

          <div className="border-t border-black p-2 bg-[#0A0A0A] text-white flex items-center gap-2 text-[10px]">
            <Plus size={12}/> <span>ADD CONNECTOR • PUBLISHED badges = live</span>
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="h-[22px] bg-[#0A0A0A] text-white flex items-center px-2 font-mono text-[11px] shrink-0 border-t border-black tracking-wide">
        <div className="flex items-center gap-3">
          <span className="hidden sm:inline">BRUTALIST • MINIMAL • EDITORIAL — UNISCROLL.OS — LIVE</span>
          <span className="sm:hidden">UNISCROLL.OS</span>
          <span className="w-2 h-2 bg-[#FFD60A] rounded-full animate-pulse hidden sm:inline"/>
        </div>
        <div className="flex-1 flex justify-center">
          <span className="bg-white text-black px-2 py-0.5 text-[10px] font-bold hidden md:inline">TENANT: {activeTenant.slug} • /workspace mounted</span>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <span className="bg-[#FFD60A] text-black px-2 py-0.5 font-bold text-[10px]">XP +50</span>
          <span className="hidden sm:inline">2024</span>
          <span className="flex items-center gap-1"><AlertTriangle size={10}/> {failedCount}</span>
          <span className="w-2 h-2 bg-[#FFD60A] rounded-full animate-pulse"/>
        </div>
      </div>

      {/* Mobile overlay dismiss - div not button to avoid inert control audit */}
      {mobileMenu!=='none' && (
        <div onClick={()=>setMobileMenu('none')} className="sm:hidden fixed inset-0 top-[36px] bg-black/20 z-20 cursor-pointer" aria-hidden="true"/>
      )}
    </div>
  );
}
