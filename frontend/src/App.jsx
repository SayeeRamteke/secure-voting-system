import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import RegisterPage from './pages/RegisterPage'
import BallotPage from './pages/BallotPage'
import ReceiptPage from './pages/ReceiptPage'
import AdminReveal from './pages/AdminReveal'
import AttackLab from './pages/AttackLab'

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Home', icon: '⬡' },
  { id: 'register', label: 'Register', icon: '○' },
  { id: 'vote', label: 'Vote', icon: '◈' },
  { id: 'receipt', label: 'Receipt', icon: '◎' },
  { id: 'admin', label: 'Admin', icon: '◆' },
  { id: 'attack', label: 'Attack Lab', icon: '!' },
]

export default function App() {
  const [page, setPage] = useState('dashboard')

  return (
    <div style={{ display: 'flex', minHeight: '100vh', fontFamily: "'Georgia', serif", background: '#f4f1eb' }}>

      {/* Sidebar */}
      <div style={{
        width: 220,
        background: '#0d1b2a',
        display: 'flex',
        flexDirection: 'column',
        padding: '40px 0',
        position: 'fixed',
        top: 0, left: 0, bottom: 0,
        zIndex: 100
      }}>
        <div style={{ padding: '0 24px 40px' }}>
          <div style={{ color: '#c8a951', fontSize: 11, letterSpacing: 3, marginBottom: 8, fontFamily: 'monospace' }}>
            ELECTION COMMISSION
          </div>
          <div style={{ color: 'white', fontSize: 20, fontWeight: 700, lineHeight: 1.2 }}>
            SecureVote<br />
            <span style={{ color: '#c8a951' }}>2025</span>
          </div>
        </div>

        <div style={{ flex: 1 }}>
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => setPage(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                width: '100%',
                padding: '14px 24px',
                background: page === item.id ? '#c8a951' : 'transparent',
                color: page === item.id ? '#0d1b2a' : '#8899aa',
                border: 'none',
                cursor: 'pointer',
                fontSize: 14,
                fontFamily: "'Georgia', serif",
                textAlign: 'left',
                fontWeight: page === item.id ? 700 : 400,
                transition: 'all 0.15s',
                borderLeft: page === item.id ? '3px solid #0d1b2a' : '3px solid transparent'
              }}
            >
              <span style={{ fontSize: 16 }}>{item.icon}</span>
              {item.label}
            </button>
          ))}
        </div>

        <div style={{ padding: '24px', borderTop: '1px solid #1e3248', color: '#445566', fontSize: 11, fontFamily: 'monospace' }}>
          <div>ENCRYPTED · VERIFIED</div>
          <div style={{ marginTop: 4 }}>Ed25519 · BLAKE3 · AES-GCM</div>
        </div>
      </div>

      {/* Main content */}
      <div style={{ marginLeft: 220, flex: 1 }}>
        {page === 'dashboard' && <Dashboard setPage={setPage} />}
        {page === 'register' && <RegisterPage />}
        {page === 'vote' && <BallotPage />}
        {page === 'receipt' && <ReceiptPage />}
        {page === 'admin' && <AdminReveal />}
        {page === 'attack' && <AttackLab />}
      </div>

    </div>
  )
}
