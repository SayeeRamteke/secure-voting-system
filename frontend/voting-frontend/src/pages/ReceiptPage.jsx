import { useState } from 'react'
import api from '../api'

export default function ReceiptPage() {
  const [leafIndex, setLeafIndex] = useState('')
  const [voterSecret, setVoterSecret] = useState('')
  const [proofPath, setProofPath] = useState([])
  const [verified, setVerified] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleVerify = async () => {
    setLoading(true)
    setProofPath([])
    setVerified(null)
    try {
      const { data } = await api.post('/receipt/verify', {
        leaf_index: parseInt(leafIndex),
        voter_secret: voterSecret
      })
      setProofPath(data.proof_path)
      setVerified(data.verified)
    } catch (err) {
      setVerified(false)
    }
    setLoading(false)
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f4f1eb', padding: '64px' }}>
      <div style={{ maxWidth: 600 }}>
        <div style={{ fontFamily: 'monospace', fontSize: 11, letterSpacing: 3, color: '#8899aa', marginBottom: 12 }}>
          STEP 3 OF 3 · VOTE VERIFICATION
        </div>
        <h2 style={{ fontSize: 32, fontWeight: 700, color: '#0d1b2a', margin: '0 0 8px' }}>
          Verify your ballot
        </h2>
        <p style={{ color: '#667788', fontSize: 15, lineHeight: 1.6, margin: '0 0 48px' }}>
          Enter your receipt details to walk the Merkle proof path and
          confirm your vote is intact in the final tally.
        </p>

        <div style={{ background: 'white', padding: 40, borderTop: '3px solid #0d1b2a' }}>
          <label style={{ display: 'block', fontSize: 11, letterSpacing: 2, color: '#667788', fontFamily: 'monospace', marginBottom: 8 }}>
            LEAF INDEX
          </label>
          <input
            value={leafIndex}
            onChange={e => setLeafIndex(e.target.value)}
            placeholder="e.g. 47"
            style={{
              width: '100%', padding: '12px 14px',
              border: '1px solid #ddd', borderBottom: '2px solid #0d1b2a',
              background: '#fafafa', fontSize: 15,
              fontFamily: 'monospace', outline: 'none',
              boxSizing: 'border-box', marginBottom: 24
            }}
          />

          <label style={{ display: 'block', fontSize: 11, letterSpacing: 2, color: '#667788', fontFamily: 'monospace', marginBottom: 8 }}>
            VOTER SECRET
          </label>
          <input
            value={voterSecret}
            onChange={e => setVoterSecret(e.target.value)}
            placeholder="Paste your secret here"
            style={{
              width: '100%', padding: '12px 14px',
              border: '1px solid #ddd', borderBottom: '2px solid #0d1b2a',
              background: '#fafafa', fontSize: 13,
              fontFamily: 'monospace', outline: 'none',
              boxSizing: 'border-box', marginBottom: 32
            }}
          />

          <button
            onClick={handleVerify}
            disabled={!leafIndex || !voterSecret || loading}
            style={{
              width: '100%', padding: '16px',
              background: '#0d1b2a', color: 'white',
              border: 'none', fontSize: 13,
              letterSpacing: 2, fontFamily: 'monospace',
              cursor: 'pointer'
            }}
          >
            {loading ? 'VERIFYING...' : 'VERIFY BALLOT →'}
          </button>
        </div>

        {verified !== null && (
          <div style={{
            marginTop: 2,
            background: verified ? '#0d1b2a' : '#2a0a0a',
            padding: 32,
            borderLeft: `4px solid ${verified ? '#c8a951' : '#cc4444'}`
          }}>
            <div style={{
              color: verified ? '#c8a951' : '#cc4444',
              fontFamily: 'monospace', fontSize: 11, letterSpacing: 2, marginBottom: 20
            }}>
              {verified ? '✓ BALLOT VERIFIED — INTEGRITY CONFIRMED' : '✗ VERIFICATION FAILED — POSSIBLE TAMPERING'}
            </div>

            {proofPath.map((step, i) => (
              <div key={i} style={{
                display: 'flex', gap: 16, marginBottom: 12,
                paddingBottom: 12, borderBottom: '1px solid #1e3248',
                alignItems: 'flex-start'
              }}>
                <div style={{ color: '#c8a951', fontFamily: 'monospace', fontSize: 11, flexShrink: 0, marginTop: 2 }}>
                  L{i + 1}
                </div>
                <div style={{ fontFamily: 'monospace', fontSize: 12, color: '#5a8fa8', wordBreak: 'break-all' }}>
                  {step.hash}
                </div>
                <div style={{ color: '#c8a951', flexShrink: 0 }}>✓</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}