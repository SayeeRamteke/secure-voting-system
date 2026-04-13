import { useState } from 'react'
import api from '../api'

export default function RegisterPage() {
  const [rollNo, setRollNo] = useState('')
  const [voterSecret, setVoterSecret] = useState('')
  const [status, setStatus] = useState('')
  const [step, setStep] = useState(0)

  const handleRegister = async () => {
    if (!rollNo) return
    setStep(1)
    setStatus('Contacting server...')

    try {
      const { data: options } = await api.post('/register/begin', { roll_no: rollNo })

      options.challenge = Uint8Array.from(atob(options.challenge), c => c.charCodeAt(0))
      options.user.id = Uint8Array.from(atob(options.user.id), c => c.charCodeAt(0))

      setStep(2)
      setStatus('Waiting for Touch ID...')

      let credential
      try {
        credential = await navigator.credentials.create({ publicKey: options })
      } catch (e) {
        console.error('WebAuthn error:', e.name, e.message)
        setStatus('error: ' + e.message)
        setStep(0)
        return
      }

      if (!credential) {
        setStatus('error: no credential returned')
        setStep(0)
        return
      }

      setStep(3)
      setStatus('Finalising registration...')

      const { data } = await api.post('/register/complete', {
        roll_no: rollNo,
        attestation: {
          id: credential.id,
          rawId: btoa(String.fromCharCode(...new Uint8Array(credential.rawId))),
          response: {
            clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(credential.response.clientDataJSON))),
            attestationObject: btoa(String.fromCharCode(...new Uint8Array(credential.response.attestationObject))),
          },
          type: credential.type,
        }
      })

      setVoterSecret(data.voter_secret)
      setStep(4)
      setStatus('success')

    } catch (err) {
      console.error('Registration error:', err)
      setStatus('error: ' + err.message)
      setStep(0)
    }
  }

  const STEPS = ['Submit Roll No.', 'Server Challenge', 'Touch ID Scan', 'Confirmed']

  return (
    <div style={{ minHeight: '100vh', background: '#f4f1eb', padding: '64px' }}>
      <div style={{ maxWidth: 560 }}>

        <div style={{ fontFamily: 'monospace', fontSize: 11, letterSpacing: 3, color: '#8899aa', marginBottom: 12 }}>
          STEP 1 OF 3 · VOTER REGISTRATION
        </div>
        <h2 style={{ fontSize: 32, fontWeight: 700, color: '#0d1b2a', margin: '0 0 8px' }}>
          Register your identity
        </h2>
        <p style={{ color: '#667788', fontSize: 15, lineHeight: 1.6, margin: '0 0 48px' }}>
          Your fingerprint authenticates via Apple's Secure Enclave.
          No biometric data ever leaves your device.
        </p>

        <div style={{ display: 'flex', gap: 0, marginBottom: 48 }}>
          {STEPS.map((s, i) => (
            <div key={i} style={{ flex: 1, position: 'relative' }}>
              <div style={{
                height: 3,
                background: step > i ? '#c8a951' : '#ddd',
                transition: 'background 0.3s'
              }} />
              <div style={{
                marginTop: 8,
                fontSize: 10,
                fontFamily: 'monospace',
                color: step > i ? '#c8a951' : '#aaa',
                letterSpacing: 1
              }}>
                {s.toUpperCase()}
              </div>
            </div>
          ))}
        </div>

        <div style={{ background: 'white', padding: 40, borderTop: '3px solid #c8a951' }}>
          <label style={{
            display: 'block',
            fontSize: 11,
            letterSpacing: 2,
            color: '#667788',
            fontFamily: 'monospace',
            marginBottom: 8
          }}>
            ROLL NUMBER / VOTER ID
          </label>
          <input
            value={rollNo}
            onChange={e => setRollNo(e.target.value)}
            placeholder="e.g. CS2021001"
            style={{
              width: '100%',
              padding: '14px 16px',
              border: '1px solid #ddd',
              borderBottom: '2px solid #0d1b2a',
              background: '#fafafa',
              fontSize: 16,
              fontFamily: "'Georgia', serif",
              outline: 'none',
              boxSizing: 'border-box',
              marginBottom: 32
            }}
          />

          <button
            onClick={handleRegister}
            disabled={!rollNo || step > 0}
            style={{
              width: '100%',
              padding: '16px',
              background: !rollNo || step > 0 ? '#ddd' : '#0d1b2a',
              color: !rollNo || step > 0 ? '#aaa' : 'white',
              border: 'none',
              fontSize: 13,
              letterSpacing: 2,
              fontFamily: 'monospace',
              cursor: !rollNo || step > 0 ? 'default' : 'pointer',
              transition: 'all 0.2s'
            }}
          >
            {step === 0 ? 'REGISTER WITH TOUCH ID →' : status.toUpperCase()}
          </button>
        </div>

        {voterSecret && (
          <div style={{
            marginTop: 2,
            background: '#0d1b2a',
            padding: 32,
            borderLeft: '3px solid #c8a951'
          }}>
            <div style={{ color: '#c8a951', fontSize: 11, letterSpacing: 2, fontFamily: 'monospace', marginBottom: 12 }}>
              ✓ REGISTRATION COMPLETE — SAVE THIS SECRET
            </div>
            <div style={{
              fontFamily: 'monospace',
              fontSize: 13,
              color: '#8fc8b0',
              wordBreak: 'break-all',
              lineHeight: 1.8,
              background: '#0a1520',
              padding: 16
            }}>
              {voterSecret}
            </div>
            <p style={{ color: '#667788', fontSize: 12, marginTop: 16, lineHeight: 1.6 }}>
              This secret is needed to verify your vote on the Receipt page.
              Store it somewhere safe — it cannot be recovered.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}