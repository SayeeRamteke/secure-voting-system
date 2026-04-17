const FEATURES = [
  { icon: '◈', title: 'Biometric Auth', desc: 'Touch ID via WebAuthn. Your fingerprint never leaves the device.' },
  { icon: '⬡', title: 'Merkle Integrity', desc: 'Every vote is a leaf in a cryptographic tree. Tampering is mathematically detectable.' },
  { icon: '◎', title: 'Zero-Knowledge Receipt', desc: 'Verify your vote was counted without revealing who you voted for.' },
  { icon: '◆', title: 'Shamir Secret Sharing', desc: 'Results require 2 of 3 keyholders. No single party controls the outcome.' },
]

export default function Dashboard({ setPage }) {
  return (
    <div style={{ minHeight: '100vh', background: '#f4f1eb' }}>

      {/* Hero */}
      <div style={{
        background: '#0d1b2a',
        padding: '80px 64px',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute', top: 0, right: 0, bottom: 0, left: 0,
          backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 40px, #ffffff04 40px, #ffffff04 41px), repeating-linear-gradient(90deg, transparent, transparent 40px, #ffffff04 40px, #ffffff04 41px)',
          pointerEvents: 'none'
        }} />
        <div style={{ color: '#c8a951', fontSize: 11, letterSpacing: 4, marginBottom: 20, fontFamily: 'monospace' }}>
          GENERAL ELECTION · 2025
        </div>
        <h1 style={{
          color: 'white',
          fontSize: 52,
          fontWeight: 700,
          margin: '0 0 16px',
          lineHeight: 1.15,
          maxWidth: 600
        }}>
          Secure<br />
          <span style={{ color: '#c8a951' }}>Voting</span> System.
        </h1>
        <p style={{ color: '#8899aa', fontSize: 16, maxWidth: 480, lineHeight: 1.7, margin: '0 0 40px' }}>
          End-to-end encrypted digital voting with hardware biometric authentication,
          Merkle tree integrity proofs, and threshold cryptography for result decryption.
        </p>
        <div style={{ display: 'flex', gap: 12 }}>
          <button
            onClick={() => setPage('register')}
            style={{
              padding: '14px 28px',
              background: '#c8a951',
              color: '#0d1b2a',
              border: 'none',
              fontSize: 14,
              fontWeight: 700,
              cursor: 'pointer',
              fontFamily: "'Georgia', serif",
              letterSpacing: 1
            }}
          >
            REGISTER TO VOTE →
          </button>
          <button
            onClick={() => setPage('vote')}
            style={{
              padding: '14px 28px',
              background: 'transparent',
              color: '#8899aa',
              border: '1px solid #2a3f55',
              fontSize: 14,
              cursor: 'pointer',
              fontFamily: "'Georgia', serif"
            }}
          >
            Cast Your Vote
          </button>
        </div>
      </div>

      {/* Features */}
      <div style={{ padding: '64px' }}>
        <div style={{
          fontSize: 11,
          letterSpacing: 3,
          color: '#8899aa',
          marginBottom: 32,
          fontFamily: 'monospace'
        }}>
          SECURITY ARCHITECTURE
        </div>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: 2
        }}>
          {FEATURES.map((f, i) => (
            <div key={i} style={{
              background: 'white',
              padding: '32px',
              borderLeft: '3px solid #c8a951'
            }}>
              <div style={{ fontSize: 24, marginBottom: 12, color: '#0d1b2a' }}>{f.icon}</div>
              <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 8, color: '#0d1b2a' }}>{f.title}</div>
              <div style={{ color: '#667788', fontSize: 14, lineHeight: 1.6 }}>{f.desc}</div>
            </div>
          ))}
        </div>

        {/* Status bar */}
        <div style={{
          marginTop: 2,
          background: '#0d1b2a',
          padding: '20px 32px',
          display: 'flex',
          gap: 40
        }}>
          {[
            { label: 'ENCRYPTION', value: 'AES-256-GCM' },
            { label: 'SIGNATURE', value: 'Ed25519' },
            { label: 'HASH', value: 'BLAKE3' },
            { label: 'INTEGRITY', value: 'Merkle Tree' },
          ].map((s, i) => (
            <div key={i}>
              <div style={{ color: '#445566', fontSize: 10, letterSpacing: 2, fontFamily: 'monospace' }}>{s.label}</div>
              <div style={{ color: '#c8a951', fontSize: 13, fontFamily: 'monospace', marginTop: 4 }}>{s.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}