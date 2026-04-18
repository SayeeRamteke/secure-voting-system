import { useEffect, useState } from 'react'
import api from '../api'

const STATUS_COLOR = {
  attack: '#cc4444',
  blocked: '#c8a951',
  defended: '#8fc8b0',
  observed: '#5a8fa8',
  passed: '#c8a951',
  dry_run: '#8899aa',
  failed: '#ff6b6b'
}

export default function AttackLab() {
  const [scenarios, setScenarios] = useState([])
  const [selected, setSelected] = useState('credential_stuffing')
  const [rollNo, setRollNo] = useState('')
  const [pin, setPin] = useState('')
  const [allowLiveProbe, setAllowLiveProbe] = useState(false)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/attack/scenarios')
      .then(({ data }) => {
        setScenarios(data.scenarios)
        if (data.scenarios?.[0]) setSelected(data.scenarios[0].id)
      })
      .catch(err => setError(err.response?.data?.detail || err.message))
  }, [])

  const scenario = scenarios.find(item => item.id === selected)

  const runScenario = async () => {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const { data } = await api.post('/attack/run', {
        scenario_id: selected,
        roll_no: rollNo || null,
        pin: pin || null,
        allow_live_probe: allowLiveProbe
      })
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    }
    setLoading(false)
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f4f1eb', padding: '64px' }}>
      <div style={{ maxWidth: 980 }}>
        <div style={{ fontFamily: 'monospace', fontSize: 11, letterSpacing: 3, color: '#8899aa', marginBottom: 12 }}>
          ATTACK LAB · LOCAL SIMULATION
        </div>
        <h2 style={{ fontSize: 32, fontWeight: 700, color: '#0d1b2a', margin: '0 0 8px' }}>
          Test the defenses
        </h2>
        <p style={{ color: '#667788', fontSize: 15, lineHeight: 1.6, margin: '0 0 40px', maxWidth: 720 }}>
          Run controlled attacks against the local election pipeline. The lab uses live state where it is safe,
          and marks destructive probes before they run.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 28, alignItems: 'start' }}>
          <div>
            {scenarios.map(item => (
              <button
                key={item.id}
                onClick={() => {
                  setSelected(item.id)
                  setResult(null)
                  setError('')
                }}
                style={{
                  width: '100%',
                  display: 'block',
                  textAlign: 'left',
                  background: selected === item.id ? '#0d1b2a' : 'white',
                  color: selected === item.id ? 'white' : '#0d1b2a',
                  border: 'none',
                  borderLeft: `4px solid ${selected === item.id ? '#c8a951' : 'transparent'}`,
                  padding: '18px 20px',
                  marginBottom: 2,
                  cursor: 'pointer'
                }}
              >
                <div style={{ fontWeight: 700, fontSize: 15 }}>{item.title}</div>
                <div style={{
                  marginTop: 6,
                  color: selected === item.id ? '#8899aa' : '#667788',
                  fontSize: 12,
                  lineHeight: 1.5
                }}>
                  {item.defense}
                </div>
              </button>
            ))}
          </div>

          <div>
            <div style={{ background: 'white', padding: 32, borderTop: '3px solid #8a1a1a' }}>
              <div style={{ color: '#8a1a1a', fontFamily: 'monospace', fontSize: 11, letterSpacing: 2, marginBottom: 12 }}>
                SELECTED ATTACK
              </div>
              <h3 style={{ margin: '0 0 10px', color: '#0d1b2a', fontSize: 24 }}>
                {scenario?.title || 'Loading...'}
              </h3>
              <p style={{ color: '#667788', lineHeight: 1.6, margin: '0 0 24px' }}>
                {scenario?.attack}
              </p>

              {selected === 'credential_stuffing' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 24 }}>
                  <div>
                    <label style={{ display: 'block', fontSize: 11, letterSpacing: 2, color: '#667788', fontFamily: 'monospace', marginBottom: 8 }}>
                      ROLL NUMBER
                    </label>
                    <input
                      value={rollNo}
                      onChange={e => setRollNo(e.target.value)}
                      placeholder="e.g. 101"
                      autoComplete="off"
                      style={{
                        width: '100%',
                        padding: '12px 14px',
                        border: '1px solid #ddd',
                        borderBottom: '2px solid #0d1b2a',
                        background: '#fafafa',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ display: 'block', fontSize: 11, letterSpacing: 2, color: '#667788', fontFamily: 'monospace', marginBottom: 8 }}>
                      LEAKED PIN
                    </label>
                    <input
                      value={pin}
                      onChange={e => setPin(e.target.value.replace(/\D/g, '').slice(0, 12))}
                      placeholder="e.g. 1234"
                      type="password"
                      inputMode="numeric"
                      autoComplete="off"
                      data-lpignore="true"
                      style={{
                        width: '100%',
                        padding: '12px 14px',
                        border: '1px solid #ddd',
                        borderBottom: '2px solid #0d1b2a',
                        background: '#fafafa',
                        boxSizing: 'border-box'
                      }}
                    />
                  </div>
                </div>
              )}

              {scenario?.live_probe && (
                <label style={{ display: 'flex', gap: 10, alignItems: 'center', color: '#667788', fontSize: 13, marginBottom: 24 }}>
                  <input
                    type="checkbox"
                    checked={allowLiveProbe}
                    onChange={e => setAllowLiveProbe(e.target.checked)}
                  />
                  Allow live probe against local DB
                </label>
              )}

              <button
                onClick={runScenario}
                disabled={loading || !selected}
                style={{
                  width: '100%',
                  padding: '16px',
                  background: '#8a1a1a',
                  color: 'white',
                  border: 'none',
                  fontSize: 13,
                  letterSpacing: 2,
                  fontFamily: 'monospace',
                  cursor: loading ? 'default' : 'pointer'
                }}
              >
                {loading ? 'RUNNING...' : 'RUN ATTACK SIMULATION'}
              </button>

              {error && (
                <div style={{ marginTop: 16, color: '#8a1a1a', fontFamily: 'monospace', fontSize: 12 }}>
                  {error}
                </div>
              )}
            </div>

            {result && (
              <div style={{ marginTop: 2, background: '#0d1b2a', padding: 32 }}>
                <div style={{
                  color: result.verdict === 'defended' ? '#c8a951' : result.verdict === 'vulnerable' ? '#ff6b6b' : '#8899aa',
                  fontFamily: 'monospace',
                  fontSize: 11,
                  letterSpacing: 2,
                  marginBottom: 14
                }}>
                  VERDICT · {result.verdict.toUpperCase()}
                </div>
                <div style={{ color: 'white', fontSize: 22, fontWeight: 700, marginBottom: 22 }}>
                  {result.summary}
                </div>

                {result.events.map((event, i) => (
                  <div key={i} style={{
                    display: 'grid',
                    gridTemplateColumns: '96px 1fr',
                    gap: 18,
                    borderTop: i === 0 ? '1px solid #1e3248' : 'none',
                    borderBottom: '1px solid #1e3248',
                    padding: '16px 0'
                  }}>
                    <div style={{ color: STATUS_COLOR[event.status] || '#8899aa', fontFamily: 'monospace', fontSize: 11 }}>
                      {event.status.toUpperCase()}
                    </div>
                    <div>
                      <div style={{ color: '#c8a951', fontWeight: 700, marginBottom: 4 }}>{event.title}</div>
                      <div style={{ color: '#667788', lineHeight: 1.55, fontSize: 13 }}>{event.detail}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
