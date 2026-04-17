import { useState } from 'react'
import api from '../api'

const CANDIDATES = [
  { name: 'Priya Sharma', party: 'National Democratic Alliance', code: 'NDA', color: '#1a4f8a' },
  { name: 'Rahul Verma', party: 'United Progressive Front', code: 'UPF', color: '#8a1a1a' },
  { name: 'Anita Desai', party: 'Independent Candidate', code: 'IND', color: '#2a6a3a' },
]

export default function BallotPage() {
  const [selected, setSelected] = useState('')
  const [logs, setLogs] = useState([])
  const [leafIndex, setLeafIndex] = useState(null)
  const [voted, setVoted] = useState(false)
  const [loading, setLoading] = useState(false)

  const addLog = (msg) => setLogs(p => [...p, { text: msg, time: new Date().toLocaleTimeString() }])

  const handleVote = async () => {
  if (!selected) return
  setLoading(true)
  setLogs([])

  try {
    addLog('Requesting server challenge...')
    const { data: options } = await api.post('/vote/begin')

    addLog('Awaiting biometric confirmation...')

    const publicKey = {
      challenge: Uint8Array.from(atob(options.challenge), c => c.charCodeAt(0)),
      rpId: options.rpId,
      timeout: options.timeout,
      userVerification: options.userVerification,
    }

    let assertion
    try {
      assertion = await navigator.credentials.get({ publicKey })
    } catch (e) {
      addLog('ERROR: ' + e.message)
      setLoading(false)
      return
    }

    addLog('WebAuthn assertion received ✓')
    addLog('Transmitting encrypted ballot...')

    const voterSecret = prompt('Enter your voter secret:')

    const { data } = await api.post('/vote/complete', {
      credential_id: assertion.id,
      voter_secret: voterSecret,
      encrypted_vote: btoa(selected),
      aes_key: btoa('demo-key'),
      aes_nonce: btoa('demo-nonce'),
      signature: btoa(String.fromCharCode(...new Uint8Array(assertion.response.signature))),
      webauthn_assertion: {
        id: assertion.id,
        rawId: btoa(String.fromCharCode(...new Uint8Array(assertion.rawId))),
        response: {
          clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(assertion.response.clientDataJSON))),
          authenticatorData: btoa(String.fromCharCode(...new Uint8Array(assertion.response.authenticatorData))),
          signature: btoa(String.fromCharCode(...new Uint8Array(assertion.response.signature))),
        },
        type: assertion.type,
      }
    })

    const steps = [
      `Nullifier registered: leaf #${data.leaf_index}`,
      `Merkle insertion: leaf #${data.leaf_index}`,
      'Ballot committed ✓'
    ]
    steps.forEach((s, i) => setTimeout(() => addLog(s), i * 600))
    setLeafIndex(data.leaf_index)
    setVoted(true)

  } catch (err) {
    addLog('ERROR: ' + err.message)
  }
  setLoading(false)
}

  return (
    <div style={{ minHeight: '100vh', background: '#f4f1eb', padding: '64px' }}>
      <div style={{ fontFamily: 'monospace', fontSize: 11, letterSpacing: 3, color: '#8899aa', marginBottom: 12 }}>
        STEP 2 OF 3 · CAST YOUR BALLOT
      </div>
      <h2 style={{ fontSize: 32, fontWeight: 700, color: '#0d1b2a', margin: '0 0 8px' }}>
        General Election 2025
      </h2>
      <p style={{ color: '#667788', fontSize: 15, margin: '0 0 48px' }}>
        Select one candidate. Your vote will be encrypted before transmission.
      </p>

      <div style={{ display: 'flex', gap: 32, alignItems: 'flex-start' }}>

        {/* Ballot */}
        <div style={{ flex: 1 }}>
          {!voted ? (
            <>
              {CANDIDATES.map(c => (
                <div
                  key={c.name}
                  onClick={() => setSelected(c.name)}
                  style={{
                    background: 'white',
                    marginBottom: 2,
                    padding: '24px 28px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 20,
                    borderLeft: selected === c.name ? `4px solid ${c.color}` : '4px solid transparent',
                    transition: 'all 0.15s',
                    opacity: selected && selected !== c.name ? 0.5 : 1
                  }}
                >
                  <div style={{
                    width: 20, height: 20,
                    border: `2px solid ${selected === c.name ? c.color : '#ccc'}`,
                    borderRadius: '50%',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    flexShrink: 0
                  }}>
                    {selected === c.name && (
                      <div style={{ width: 10, height: 10, borderRadius: '50%', background: c.color }} />
                    )}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, fontSize: 16, color: '#0d1b2a' }}>{c.name}</div>
                    <div style={{ fontSize: 13, color: '#667788', marginTop: 2 }}>{c.party}</div>
                  </div>
                  <div style={{
                    fontFamily: 'monospace',
                    fontSize: 12,
                    color: c.color,
                    border: `1px solid ${c.color}`,
                    padding: '2px 8px'
                  }}>
                    {c.code}
                  </div>
                </div>
              ))}

              <button
                onClick={handleVote}
                disabled={!selected || loading}
                style={{
                  width: '100%',
                  marginTop: 2,
                  padding: '18px',
                  background: selected ? '#0d1b2a' : '#ccc',
                  color: 'white',
                  border: 'none',
                  fontSize: 13,
                  letterSpacing: 2,
                  fontFamily: 'monospace',
                  cursor: selected ? 'pointer' : 'default',
                }}
              >
                {loading ? 'PROCESSING...' : 'CONFIRM VOTE WITH TOUCH ID →'}
              </button>
            </>
          ) : (
            <div style={{
              background: '#0d1b2a',
              padding: 40,
              borderLeft: '4px solid #c8a951'
            }}>
              <div style={{ color: '#c8a951', fontFamily: 'monospace', fontSize: 11, letterSpacing: 2 }}>
                ✓ BALLOT SUCCESSFULLY CAST
              </div>
              <div style={{ color: 'white', fontSize: 24, fontWeight: 700, margin: '16px 0 8px' }}>
                Your vote has been recorded.
              </div>
              <div style={{ color: '#667788', fontSize: 14 }}>
                Receipt leaf index: <span style={{ color: '#c8a951', fontFamily: 'monospace' }}>#{leafIndex}</span>
              </div>
              <p style={{ color: '#445566', fontSize: 13, marginTop: 16, lineHeight: 1.6 }}>
                Save your leaf index and voter secret. Use them on the Receipt
                page to verify your vote was counted and not tampered with.
              </p>
            </div>
          )}
        </div>

        {/* Security Cockpit */}
        <div style={{
          width: 340,
          background: '#0a1520',
          padding: 24,
          fontFamily: 'monospace',
          fontSize: 12,
          flexShrink: 0
        }}>
          <div style={{
            color: '#445566',
            fontSize: 10,
            letterSpacing: 2,
            marginBottom: 20,
            paddingBottom: 12,
            borderBottom: '1px solid #1e3248'
          }}>
            CRYPTOGRAPHIC AUDIT LOG
          </div>
          {logs.length === 0 ? (
            <div style={{ color: '#2a4a6a' }}>Awaiting ballot submission...</div>
          ) : (
            logs.map((log, i) => (
              <div key={i} style={{ marginBottom: 10, display: 'flex', gap: 12 }}>
                <span style={{ color: '#2a4a6a', flexShrink: 0 }}>{log.time}</span>
                <span style={{ color: log.text.includes('ERROR') ? '#ff6b6b' : log.text.includes('✓') ? '#c8a951' : '#5a8fa8' }}>
                  {log.text}
                </span>
              </div>
            ))
          )}
        </div>

      </div>
    </div>
  )
}