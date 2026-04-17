import { useState } from 'react'
import api from '../api'

export default function AdminReveal() {
  const [shards, setShards] = useState(['', '', ''])
  const [results, setResults] = useState(null)
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)

  const updateShard = (i, v) => {
    const s = [...shards]; s[i] = v; setShards(s)
  }

  const handleReveal = async () => {
    setLoading(true)
    setStatus('Combining cryptographic shards...')
    try {
      const { data } = await api.post('/admin/reveal', { shards })
      setResults(data.results)
      setStatus('Results decrypted successfully.')
    } catch (err) {
      setStatus('Error: ' + err.message)
    }
    setLoading(false)
  }

  const total = results ? Object.values(results).reduce((a, b) => a + b, 0) : 0
  const maxVotes = results ? Math.max(...Object.values(results)) : 0

  return (
    <div style={{ minHeight: '100vh', background: '#f4f1eb', padding: '64px' }}>
      <div style={{ maxWidth: 600 }}>
        <div style={{ fontFamily: 'monospace', fontSize: 11, letterSpacing: 3, color: '#8899aa', marginBottom: 12 }}>
          ADMIN · RESTRICTED ACCESS
        </div>
        <h2 style={{ fontSize: 32, fontWeight: 700, color: '#0d1b2a', margin: '0 0 8px' }}>
          Reveal election results
        </h2>
        <p style={{ color: '#667788', fontSize: 15, lineHeight: 1.6, margin: '0 0 48px' }}>
          Provide any 2 of 3 Shamir key shards to decrypt the final tally.
          No single keyholder can access results alone.
        </p>

        <div style={{ background: 'white', padding: 40, borderTop: '3px solid #8a1a1a' }}>
          {shards.map((shard, i) => (
            <div key={i} style={{ marginBottom: 24 }}>
              <label style={{
                display: 'block', fontSize: 11, letterSpacing: 2,
                color: '#667788', fontFamily: 'monospace', marginBottom: 8
              }}>
                SHARD {i + 1} OF 3
              </label>
              <textarea
                value={shard}
                onChange={e => updateShard(i, e.target.value)}
                placeholder={`Keyholder ${i + 1} pastes their hex shard here`}
                style={{
                  width: '100%', height: 80, padding: '12px 14px',
                  border: '1px solid #ddd', borderBottom: shard ? '2px solid #0d1b2a' : '2px solid #ddd',
                  background: '#fafafa', fontFamily: 'monospace',
                  fontSize: 12, resize: 'none', outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>
          ))}

          <button
            onClick={handleReveal}
            disabled={loading}
            style={{
              width: '100%', padding: '16px',
              background: '#8a1a1a', color: 'white',
              border: 'none', fontSize: 13,
              letterSpacing: 2, fontFamily: 'monospace',
              cursor: 'pointer'
            }}
          >
            {loading ? 'DECRYPTING...' : 'COMBINE SHARDS & REVEAL →'}
          </button>

          {status && (
            <p style={{ marginTop: 16, fontFamily: 'monospace', fontSize: 12, color: '#667788' }}>
              {status}
            </p>
          )}
        </div>

        {results && (
          <div style={{ marginTop: 2, background: '#0d1b2a', padding: 40 }}>
            <div style={{ color: '#c8a951', fontFamily: 'monospace', fontSize: 11, letterSpacing: 2, marginBottom: 28 }}>
              ✓ OFFICIAL RESULTS · GENERAL ELECTION 2025
            </div>
            {Object.entries(results)
              .sort((a, b) => b[1] - a[1])
              .map(([candidate, count], i) => (
                <div key={candidate} style={{ marginBottom: 24 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span style={{ color: i === 0 ? 'white' : '#667788', fontWeight: i === 0 ? 700 : 400 }}>
                      {i === 0 ? '◆ ' : '○ '}{candidate}
                    </span>
                    <span style={{ fontFamily: 'monospace', color: '#c8a951', fontSize: 13 }}>
                      {count} votes · {Math.round((count / total) * 100)}%
                    </span>
                  </div>
                  <div style={{ height: 6, background: '#1e3248', borderRadius: 0 }}>
                    <div style={{
                      height: '100%',
                      width: `${(count / maxVotes) * 100}%`,
                      background: i === 0 ? '#c8a951' : '#2a4a6a',
                      transition: 'width 1s ease'
                    }} />
                  </div>
                </div>
              ))}
            <div style={{
              marginTop: 28, paddingTop: 20,
              borderTop: '1px solid #1e3248',
              fontFamily: 'monospace', fontSize: 11,
              color: '#445566'
            }}>
              TOTAL VOTES CAST: {total} · INTEGRITY: MERKLE VERIFIED
            </div>
          </div>
        )}
      </div>
    </div>
  )
}