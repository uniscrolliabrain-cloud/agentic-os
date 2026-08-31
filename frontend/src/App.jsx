import { useEffect, useRef, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || ''

function App() {
  const [conversations, setConversations] = useState([])
  const [currentConvId, setCurrentConvId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [state, setState] = useState({ role: 'director', event_count: 0 })
  const [showEvents, setShowEvents] = useState(false)
  const [events, setEvents] = useState([])

  // Multi-tenant
  const [tenants, setTenants] = useState([])
  const [activeTenant, setActiveTenant] = useState(null)
  const [skills, setSkills] = useState([])
  const [tools, setTools] = useState([])
  const [execResult, setExecResult] = useState(null)
  const [showExec, setShowExec] = useState(false)
  const [background, setBackground] = useState(null)

  // FASE 6: tabs de cliente — Briefings (Drive), Hoy (artifacts), Calendario (schedules), Drafts
  const [activeTab, setActiveTab] = useState('chat')
  const [schedules, setSchedules] = useState([])
  const [drafts, setDrafts] = useState([])
  const [artifacts, setArtifacts] = useState([])
  const [newSchedule, setNewSchedule] = useState({ pipeline_id: 'inbox_watcher', interval_minutes: 30, hour: '' })

  const bottomRef = useRef(null)

  // FASE 4: el tenant activo viaja en la cabecera X-Tenant-Id, nunca en el body
  function headersWithTenant(extra = {}) {
    const h = { ...extra }
    if (activeTenant) h['X-Tenant-Id'] = activeTenant
    return h
  }

  useEffect(() => {
    fetchState()
    fetchEvents()
    fetchConversations()
    fetchTenants()
    fetchSkills()
    fetchTools()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function fetchState() {
    try {
      const res = await fetch(`${API_BASE}/api/state`, { headers: headersWithTenant() })
      if (res.ok) setState(await res.json())
    } catch (e) { console.error(e) }
  }

  async function fetchEvents() {
    try {
      const res = await fetch(`${API_BASE}/api/events`, { headers: headersWithTenant() })
      if (res.ok) setEvents(await res.json())
    } catch (e) { console.error(e) }
  }

  async function fetchConversations() {
    try {
      const res = await fetch(`${API_BASE}/api/conversations`, { headers: headersWithTenant() })
      if (res.ok) setConversations(await res.json())
    } catch (e) { console.error(e) }
  }

  async function fetchTenants() {
    try {
      const res = await fetch(`${API_BASE}/api/tenants`)
      if (res.ok) {
        const data = await res.json()
        setTenants(data)
        if (data.length > 0 && !activeTenant) setActiveTenant(data[0].id)
      }
    } catch (e) { console.error(e) }
  }

  async function fetchSkills() {
    try {
      const res = await fetch(`${API_BASE}/api/skills`)
      if (res.ok) setSkills(await res.json())
    } catch (e) { console.error(e) }
  }

  async function fetchTools() {
    try {
      const res = await fetch(`${API_BASE}/api/tools`)
      if (res.ok) setTools(await res.json())
    } catch (e) { console.error(e) }
  }

  // FASE 6: scheduler + drafts + artifacts (siempre por tenant via cabecera)
  async function fetchSchedules() {
    try {
      const res = await fetch(`${API_BASE}/api/schedules`, { headers: headersWithTenant() })
      if (res.ok) setSchedules(await res.json())
    } catch (e) { console.error(e) }
  }

  async function fetchDrafts() {
    try {
      const res = await fetch(`${API_BASE}/api/drafts`, { headers: headersWithTenant() })
      if (res.ok) setDrafts(await res.json())
    } catch (e) { console.error(e) }
  }

  async function fetchArtifacts() {
    try {
      const res = await fetch(`${API_BASE}/api/artifacts`, { headers: headersWithTenant() })
      if (res.ok) setArtifacts(await res.json())
    } catch (e) { console.error(e) }
  }

  async function createSchedule(e) {
    e.preventDefault()
    const body = {
      pipeline_id: newSchedule.pipeline_id,
      interval_minutes: newSchedule.interval_minutes ? Number(newSchedule.interval_minutes) : null,
      hour: newSchedule.hour ? Number(newSchedule.hour) : null,
    }
    try {
      const res = await fetch(`${API_BASE}/api/schedules`, {
        method: 'POST',
        headers: headersWithTenant({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(body),
      })
      if (res.ok) {
        setNewSchedule({ pipeline_id: 'inbox_watcher', interval_minutes: 30, hour: '' })
        fetchSchedules()
      }
    } catch (e) { console.error(e) }
  }

  async function deleteSchedule(id) {
    try {
      const res = await fetch(`${API_BASE}/api/schedules/${id}`, {
        method: 'DELETE',
        headers: headersWithTenant(),
      })
      if (res.ok) fetchSchedules()
    } catch (e) { console.error(e) }
  }

  // Al cambiar de tenant (o en el arranque) recargamos datos por tenant
  useEffect(() => {
    if (activeTenant) {
      fetchSchedules()
      fetchDrafts()
    }
  }, [activeTenant])

  async function newConversation() {
    try {
      const res = await fetch(`${API_BASE}/api/conversations`, { method: 'POST', headers: headersWithTenant() })
      if (res.ok) {
        const conv = await res.json()
        setCurrentConvId(conv.id)
        setMessages([])
        fetchConversations()
      }
    } catch (e) { console.error(e) }
  }

  async function openConversation(convId) {
    try {
      const res = await fetch(`${API_BASE}/api/conversations/${convId}`, { headers: headersWithTenant() })
      if (res.ok) {
        const conv = await res.json()
        setCurrentConvId(conv.id)
        setMessages(conv.messages)
      }
    } catch (e) { console.error(e) }
  }

  async function deleteConversation(convId) {
    try {
      await fetch(`${API_BASE}/api/conversations/${convId}`, { method: 'DELETE', headers: headersWithTenant() })
      if (currentConvId === convId) {
        setCurrentConvId(null)
        setMessages([])
      }
      fetchConversations()
    } catch (e) { console.error(e) }
  }

  async function createTenant() {
    const name = prompt('Nombre del cliente:')
    if (!name) return
    const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
    try {
      const res = await fetch(`${API_BASE}/api/tenants`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, slug }),
      })
      if (res.ok) {
        const t = await res.json()
        setTenants([...tenants, t])
        setActiveTenant(t.id)
      }
    } catch (e) { console.error(e) }
  }

  async function runAction(action, params) {
    if (!activeTenant) {
      alert('Selecciona un cliente primero')
      return
    }
    setExecResult({ waiting: true })
    setShowExec(true)
    try {
      const res = await fetch(`${API_BASE}/api/execute`, {
        method: 'POST',
        headers: headersWithTenant({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ action, params }),
      })
      const data = await res.json()
      setExecResult(data)
      fetchState()
      fetchEvents()
    } catch (e) {
      setExecResult({ success: false, error: String(e) })
    }
  }

  async function handleSend(e) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    let convId = currentConvId
    if (!convId) {
      try {
        const res = await fetch(`${API_BASE}/api/conversations`, { method: 'POST', headers: headersWithTenant() })
        if (res.ok) {
          const conv = await res.json()
          convId = conv.id
          setCurrentConvId(conv.id)
          fetchConversations()
        }
      } catch (err) { console.error(err) }
    }

    setMessages((m) => [...m, { role: 'user', content: text }])
    setInput('')
    setLoading(true)

    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 50_000)

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: headersWithTenant({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ message: text, conversation_id: convId }),
        signal: controller.signal,
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Error del servidor')
      }
      const data = await res.json()
      setMessages((m) => [...m, { role: 'assistant', content: data.reply }])
      fetchState()
      if (data.processing && data.task_id) {
        setBackground({ id: data.task_id })
        pollBackground(data.task_id)
      } else {
        fetchEvents()
      }
    } catch (err) {
      const msg =
        err.name === 'AbortError'
          ? '⚠️ El asistente tardó demasiado en responder. Inténtalo de nuevo.'
          : `⚠️ ${err.message}`
      setMessages((m) => [...m, { role: 'assistant', content: msg }])
    } finally {
      clearTimeout(timeout)
      setLoading(false)
    }
  }

  async function pollBackground(taskId, attempts = 30) {
    try {
      const res = await fetch(`${API_BASE}/api/tasks`)
      if (!res.ok) throw new Error('error')
      const tasks = await res.json()
      const t = tasks.find((x) => x.id === taskId)
      if (!t) {
        setBackground(null)
        fetchEvents()
        fetchState()
        return
      }
      if (t.status === 'completed' || t.status === 'failed') {
        setBackground(null)
        fetchEvents()
        fetchState()
        return
      }
    } catch (e) {
      setBackground(null)
      return
    }
    if (attempts <= 0) {
      setBackground(null)
      fetchEvents()
      fetchState()
      return
    }
    setTimeout(() => pollBackground(taskId, attempts - 1), 2000)
  }

  return (
    <div className="flex h-screen bg-[#0e0e0e] text-[#e5e5e5]">
      {/* Sidebar */}
      <aside className="w-72 shrink-0 bg-[#111111] border-r border-[#222] flex flex-col">
        <div className="p-4">
          <h2 className="text-sm font-bold tracking-wide mb-4">
            AGENTE OS <span className="text-yellow-400">●</span>
          </h2>

          {/* Selector de cliente (tenant) */}
          <label className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-1">
            Cliente activo
          </label>
          <select
            value={activeTenant || ''}
            onChange={(e) => setActiveTenant(e.target.value)}
            className="w-full bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-3 py-2 text-sm text-gray-200 mb-2 focus:outline-none focus:ring-2 focus:ring-yellow-400/50"
          >
            <option value="">— sin cliente —</option>
            {tenants.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
          <button
            onClick={createTenant}
            className="w-full bg-yellow-400 hover:bg-yellow-300 text-black font-semibold rounded-lg py-2 px-4 text-sm transition mb-4"
          >
            + Registrar cliente
          </button>

          <button
            onClick={newConversation}
            className="w-full border border-[#2a2a2a] hover:bg-[#1a1a1a] text-gray-300 font-semibold rounded-lg py-2 px-4 text-sm transition"
          >
            + Nuevo chat
          </button>
        </div>

        <div className="px-4 pb-2">
          <h3 className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-2">Conversaciones</h3>
        </div>

        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {conversations.length === 0 ? (
            <p className="text-xs text-gray-600 px-2 py-1">Sin conversaciones todavía</p>
          ) : (
            conversations.map((conv) => (
              <div
                key={conv.id}
                className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm transition ${
                  currentConvId === conv.id
                    ? 'bg-[#2a2a2a] text-white'
                    : 'text-gray-400 hover:bg-[#1a1a1a] hover:text-gray-200'
                }`}
                onClick={() => openConversation(conv.id)}
              >
                <span className="text-xs">💬</span>
                <span className="flex-1 truncate">{conv.title}</span>
                <button
                  onClick={(e) => { e.stopPropagation(); deleteConversation(conv.id) }}
                  className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 text-xs transition"
                >✕</button>
              </div>
            ))
          )}
        </div>

        {/* Skills / Tools */}
        <div className="border-t border-[#222] p-4">
          <button
            onClick={() => setShowExec((v) => !v)}
            className="w-full text-left text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-2 hover:text-gray-300"
          >
            {showExec ? '▾ Herramientas y Skills' : '▸ Herramientas y Skills'}
          </button>
          {showExec && (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              <div>
                <h4 className="text-[10px] text-gray-600 uppercase mb-1">Skills (SOPs)</h4>
                {skills.map((s) => (
                  <div key={s.name} className="text-xs text-gray-400 py-1 border-b border-[#1a1a1a]">
                    <span className="text-yellow-400">◆</span> {s.description}
                  </div>
                ))}
              </div>
              <div>
                <h4 className="text-[10px] text-gray-600 uppercase mt-2 mb-1">Actions</h4>
                {tools.map((t) => (
                  <button
                    key={t.name}
                    onClick={() => runAction(t.name, {})}
                    className="w-full text-left text-xs text-gray-300 hover:bg-[#1a1a1a] rounded px-2 py-1 transition"
                  >
                    ⚡ {t.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t border-[#222]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-yellow-400 text-black flex items-center justify-center text-xs font-bold">A</div>
            <div className="text-xs">
              <div className="font-semibold text-gray-300">Alfonso</div>
              <div className="text-gray-600">alfonso@agentic-os.io</div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="border-b border-[#222] bg-[#111111]/50 backdrop-blur px-6 py-3 flex items-center justify-between">
          <h1 className="text-sm font-semibold text-gray-300">
            AGENTE OS <span className="text-yellow-400">V5.0</span>
          </h1>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#1a1a1a] text-gray-400 border border-[#2a2a2a]">
              Cliente: <span className="text-yellow-400 font-semibold">
                {tenants.find((t) => t.id === activeTenant)?.name || '—'}
              </span>
            </span>
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#1a1a1a] text-gray-400 border border-[#2a2a2a]">
              Rol: <span className="text-yellow-400 font-semibold">{state.role}</span>
            </span>
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#1a1a1a] text-gray-400 border border-[#2a2a2a]">
              Eventos: <span className="text-emerald-400 font-semibold">{state.event_count}</span>
            </span>
            <button
              onClick={() => setShowEvents((v) => !v)}
              className="text-xs px-2.5 py-1 rounded-full bg-[#1a1a1a] text-gray-400 border border-[#2a2a2a] hover:bg-[#2a2a2a] transition"
            >
              {showEvents ? 'Ocultar log' : 'Ver log'}
            </button>

            {/* FASE 6: tabs por tenant */}
            <nav className="flex items-center gap-1 ml-2">
              {['chat', 'briefings', 'hoy', 'calendario', 'drafts'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => { setActiveTab(tab); if (tab === 'briefings') fetchArtifacts(); if (tab === 'calendario') fetchSchedules(); if (tab === 'drafts') fetchDrafts() }}
                  className={`text-xs px-3 py-1 rounded-full border transition ${
                    activeTab === tab
                      ? 'bg-yellow-400/10 border-yellow-400/40 text-yellow-400'
                      : 'bg-[#1a1a1a] border-[#2a2a2a] text-gray-400 hover:bg-[#2a2a2a]'
                  }`}
                >
                  {tab === 'chat' ? 'Chat' : tab === 'briefings' ? 'Briefings' : tab === 'hoy' ? 'Hoy' : tab === 'calendario' ? 'Calendario' : 'Drafts'}
                </button>
              ))}
            </nav>
          </div>
        </header>

        {showEvents && (
          <div className="border-b border-[#222] bg-[#111111]/40 max-h-40 overflow-y-auto px-6 py-3">
            <h2 className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider mb-2">EventLog (fuente de verdad)</h2>
            {events.length === 0 ? (
              <p className="text-xs text-gray-600">Sin eventos todavía.</p>
            ) : (
              <ul className="space-y-1">
                {events.map((ev) => (
                  <li key={ev.id} className="text-xs text-gray-400 flex gap-2">
                    <span className="text-gray-600 font-mono">{ev.at.slice(11, 19)}</span>
                    <span className="text-yellow-400 font-semibold">{ev.kind}</span>
                    <span className="text-gray-600">·</span>
                    <span className="text-gray-500">actor: {ev.actor_id}</span>
                    <span className="text-gray-600">·</span>
                    <span className="text-gray-500 truncate max-w-md">{ev.payload?.goal || ev.payload?.kind || ''}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {execResult && (
          <div className={`border-b border-[#222] px-6 py-3 text-xs font-mono ${execResult.success ? 'bg-emerald-950/30 text-emerald-300' : execResult.waiting ? 'bg-[#111111]/40 text-gray-400' : 'bg-red-950/30 text-red-300'}`}>
            {execResult.waiting ? (
              <span>⚙️ Ejecutando acción...</span>
            ) : (
              <details open>
                <summary className="cursor-pointer font-semibold">
                  {execResult.success ? '✓ Ejecución exitosa' : '✗ Error en ejecución'}
                </summary>
                <pre className="mt-1 whitespace-pre-wrap">{JSON.stringify(execResult, null, 2)}</pre>
              </details>
            )}
          </div>
        )}

        <main className="flex-1 overflow-y-auto px-6 py-6">
          {activeTab === 'chat' && (
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-16">
                <div className="text-5xl mb-4">●</div>
                <h2 className="text-xl font-semibold text-gray-200 mb-2">AGENTE OS</h2>
                <p className="text-sm text-gray-500 max-w-md mx-auto">
                  Pregúntale a AGENTE OS. El rol{' '}
                  <span className="text-yellow-400 font-semibold">director</span> propone
                  intents estructurados. La policy decide, el executor ejecuta. Todo auditable en el log.
                </p>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-[#2a2a2a] text-white rounded-br-sm'
                      : 'bg-[#1e1e1e] border border-[#2a2a2a] text-gray-200 rounded-bl-sm'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-[#1e1e1e] border border-[#2a2a2a] rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-2">
                  <span className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce [animation-delay:0.15s]" />
                  <span className="w-2 h-2 bg-yellow-400 rounded-full animate-bounce [animation-delay:0.3s]" />
                </div>
              </div>
            )}

            {background && (
              <div className="flex justify-start">
                <div className="bg-[#111] border border-emerald-800/40 rounded-full px-4 py-2 text-xs text-emerald-300 flex items-center gap-2">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                  ⚙️ Orquestador procesando en segundo plano…
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
          )}

          {/* FASE 6: paneles de cliente */}
          {activeTab !== 'chat' && (
            <div className="max-w-4xl mx-auto space-y-4">
              {activeTab === 'calendario' && (
                <section className="space-y-4">
                  <h2 className="text-lg font-semibold text-gray-200">Calendario de automatizaciones</h2>
                  <form onSubmit={createSchedule} className="bg-[#151515] border border-[#2a2a2a] rounded-xl p-4 space-y-3">
                    <div className="flex gap-3 flex-wrap">
                      <select
                        value={newSchedule.pipeline_id}
                        onChange={(e) => setNewSchedule({ ...newSchedule, pipeline_id: e.target.value })}
                        className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-3 py-2 text-sm text-gray-200"
                      >
                        <option value="inbox_watcher">inbox_watcher</option>
                        <option value="daily_social">daily_social</option>
                        <option value="leads_to_draft">leads_to_draft</option>
                      </select>
                      <input
                        type="number"
                        placeholder="intervalo (min)"
                        value={newSchedule.interval_minutes || ''}
                        onChange={(e) => setNewSchedule({ ...newSchedule, interval_minutes: e.target.value })}
                        className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-3 py-2 text-sm text-gray-200 w-36"
                      />
                      <input
                        type="number"
                        placeholder="hora (0-23)"
                        value={newSchedule.hour || ''}
                        onChange={(e) => setNewSchedule({ ...newSchedule, hour: e.target.value })}
                        className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-lg px-3 py-2 text-sm text-gray-200 w-36"
                      />
                      <button type="submit" className="px-4 py-2 rounded-lg bg-yellow-400 hover:bg-yellow-300 text-black text-sm font-semibold">
                        + Programar
                      </button>
                    </div>
                  </form>
                  <div className="space-y-2">
                    {schedules.length === 0 ? (
                      <p className="text-sm text-gray-600">Sin jobs programados para este cliente.</p>
                    ) : schedules.map((s) => (
                      <div key={s.id} className="flex items-center gap-3 bg-[#151515] border border-[#2a2a2a] rounded-lg px-4 py-3">
                        <span className="text-yellow-400">⏱</span>
                        <span className="text-sm text-gray-200 font-mono flex-1">{s.pipeline_id}</span>
                        <span className="text-xs text-gray-500">
                          {s.kind === 'daily' ? `diario ${s.hour}:00` : `cada ${s.minutes} min`}
                        </span>
                        <button onClick={() => deleteSchedule(s.id)} className="text-gray-500 hover:text-red-400 text-xs">✕</button>
                      </div>
                    ))}
                  </div>
                </section>
              )}
              {activeTab === 'drafts' && (
                <section className="space-y-3">
                  <h2 className="text-lg font-semibold text-gray-200">Borradores generados (sin enviar)</h2>
                  {drafts.length === 0 ? (
                    <p className="text-sm text-gray-600">Sin borradores. Programa inbox_watcher o leads_to_draft.</p>
                  ) : drafts.map((d) => (
                    <div key={d.id} className="bg-[#151515] border border-[#2a2a2a] rounded-lg p-4">
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-emerald-400">📝</span>
                        <span className="text-gray-200">{d.subject}</span>
                        <span className="text-gray-500 text-xs ml-auto">para {d.to} · SIMULADO</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-2 whitespace-pre-wrap">{d.body}</p>
                    </div>
                  ))}
                </section>
              )}
              {activeTab === 'briefings' && (
                <section className="space-y-3">
                  <h2 className="text-lg font-semibold text-gray-200">Briefings (Drive)</h2>
                  {artifacts.length === 0 ? (
                    <p className="text-sm text-gray-600">Sin briefings. Sincroniza contenido en la carpeta drive del cliente y programa daily_social.</p>
                  ) : artifacts.map((a) => (
                    <div key={a.id} className="bg-[#151515] border border-[#2a2a2a] rounded-lg p-4">
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-yellow-400">📄</span>
                        <span className="text-gray-200">{a.source_file || a.id}</span>
                        <span className="text-gray-500 text-xs ml-auto">{a.date} · {a.pipeline}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-2">{a.copy?.slice(0, 160)}...</p>
                      <p className="text-[10px] text-gray-600 mt-1">
                        publish: {a.publish?.status} · real: {String(a.publish?.real_execution)}
                      </p>
                    </div>
                  ))}
                </section>
              )}
              {activeTab === 'hoy' && (
                <section className="space-y-3">
                  <h2 className="text-lg font-semibold text-gray-200">Hoy</h2>
                  {artifacts.length === 0 ? (
                    <p className="text-sm text-gray-600">Sin artefactos de hoy.</p>
                  ) : (
                    artifacts.slice(0, 3).map((a) => (
                      <div key={a.id} className="bg-[#151515] border border-[#2a2a2a] rounded-lg p-4">
                        <div className="text-sm text-gray-200 font-semibold">{a.source_file || a.id}</div>
                        <p className="text-xs text-gray-500 mt-1 whitespace-pre-wrap">{a.copy?.slice(0, 300)}</p>
                      </div>
                    ))
                  )}
                </section>
              )}
            </div>
          )}
        </main>

        <footer className="border-t border-[#222] bg-[#111111]/50 backdrop-blur px-6 py-4">
          <form onSubmit={handleSend} className="max-w-3xl mx-auto flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Pregúntale a AGENTE OS..."
              className="flex-1 bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl px-4 py-3 text-sm text-gray-100 placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-yellow-400/50 focus:border-transparent transition"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="px-5 py-3 rounded-xl bg-yellow-400 hover:bg-yellow-300 disabled:opacity-40 disabled:cursor-not-allowed text-sm font-semibold text-black transition"
            >
              Enviar
            </button>
          </form>
        </footer>
      </div>
    </div>
  )
}

export default App