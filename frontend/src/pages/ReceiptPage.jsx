import { useState } from 'react'
import api from '../api'

export default function ReceiptPage() {
  const [leafIndex, setLeafIndex] = useState('')
  const [voterPin, setVoterPin] = useState('')
  const [proofPath, setProofPath] = useState([])
  const [receipt, setReceipt] = useState(null)
  const [verified, setVerified] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleVerify = async () => {
    setLoading(true)
    setProofPath([])
    setReceipt(null)
    setVerified(null)
    try {
      const parsedLeafIndex = parseInt(leafIndex)
      const { data } = await api.post('/receipt/verify', {
        leaf_index: parsedLeafIndex,
        voter_secret: voterPin
      })
      setProofPath(data.proof_path)
      setReceipt(data)
      setVerified(data.verified)
    } catch (err) {
      setVerified(false)
      setReceipt({
        reason: err.response?.data?.detail || err.message
      })
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
          Enter your receipt details to confirm your ballot is included in the
          public election board.
        </p>

        <div style={{ background: 'white', padding: 40, borderTop: '3px solid #0d1b2a' }}>
          <label style={{ display: 'block', fontSize: 11, letterSpacing: 2, color: '#667788', fontFamily: 'monospace', marginBottom: 8 }}>
            LEAF INDEX
          </label>
          <input
            value={leafIndex}
            onChange={e => setLeafIndex(e.target.value)}
            placeholder="e.g. 0"
            style={{
              width: '100%', padding: '12px 14px',
              border: '1px solid #ddd', borderBottom: '2px solid #0d1b2a',
              background: '#fafafa', fontSize: 15,
              fontFamily: 'monospace', outline: 'none',
              boxSizing: 'border-box', marginBottom: 24
            }}
          />

          <label style={{ display: 'block', fontSize: 11, letterSpacing: 2, color: '#667788', fontFamily: 'monospace', marginBottom: 8 }}>
            VOTING PIN
          </label>
          <input
            value={voterPin}
            onChange={e => setVoterPin(e.target.value.replace(/\D/g, '').slice(0, 12))}
            placeholder="Enter your PIN"
            type="password"
            inputMode="numeric"
            autoComplete="off"
            data-lpignore="true"
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
            disabled={!leafIndex || !voterPin || loading}
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
              fontFamily: 'monospace', fontSize: 11, letterSpacing: 2, marginBottom: 14
            }}>
              {verified ? 'BALLOT VERIFIED' : 'VERIFICATION FAILED'}
            </div>

            <div style={{ color: 'white', fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
              {verified ? `Ballot #${receipt?.ballot_id || parseInt(leafIndex) + 1} is in the official tally.` : 'This receipt did not match the public board.'}
            </div>

            <div style={{ color: verified ? '#667788' : '#cc8888', fontSize: 14, lineHeight: 1.6 }}>
              {verified
                ? `Checked against the published root for ${receipt?.total_votes || 0} vote${receipt?.total_votes === 1 ? '' : 's'}.`
                : receipt?.reason || 'The Ballot ID, PIN, or proof did not match the official root.'}
            </div>

            {verified && (
              <div style={{ marginTop: 18, color: '#c8a951', fontFamily: 'monospace', fontSize: 12 }}>
                Status: INCLUDED IN OFFICIAL TALLY
              </div>
            )}

            <details style={{ marginTop: 24, color: '#667788', fontSize: 12 }}>
              <summary style={{ cursor: 'pointer', color: verified ? '#c8a951' : '#cc4444', fontFamily: 'monospace' }}>
                Technical proof
              </summary>
              <div style={{ marginTop: 16 }}>
                {receipt?.published_root && (
                  <div style={{ marginBottom: 14, fontFamily: 'monospace', wordBreak: 'break-all', color: '#5a8fa8' }}>
                    Official root: {receipt.published_root}
                  </div>
                )}
                {receipt?.leaf_hash && (
                  <div style={{ marginBottom: 14, fontFamily: 'monospace', wordBreak: 'break-all', color: '#5a8fa8' }}>
                    Leaf hash: {receipt.leaf_hash}
                  </div>
                )}
                {proofPath.length === 0 && (
                  <div style={{ fontFamily: 'monospace', color: '#5a8fa8' }}>
                    No sibling hashes needed for a single-ballot tree.
                  </div>
                )}
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
                      {step.direction}: {step.hash}
                    </div>
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}
      </div>
    </div>
  )
}
