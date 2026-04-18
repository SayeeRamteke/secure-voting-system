import { useState } from 'react'
import api from '../api'

export default function RegisterPage() {
  const [rollNo, setRollNo] = useState('')
  const [pin, setPin] = useState('')
  const [confirmPin, setConfirmPin] = useState('')
  const [panicPin, setPanicPin] = useState('')
  const [confirmPanicPin, setConfirmPanicPin] = useState('')
  const [registered, setRegistered] = useState(false)
  const [status, setStatus] = useState('')
  const [step, setStep] = useState(0)

  const pinMismatch = confirmPin && pin !== confirmPin
  const wantsPanicPin = panicPin || confirmPanicPin
  const panicPinMismatch = wantsPanicPin && panicPin !== confirmPanicPin
  const panicSameAsPin = wantsPanicPin && panicPin && panicPin === pin

  const handleRegister = async () => {
    if (!rollNo || !pin || !confirmPin) return
    if (!/^\d{4,12}$/.test(pin)) {
      setStatus('error: PIN must be 4 to 12 digits')
      return
    }
    if (pin !== confirmPin) {
      setStatus('error: PINs do not match')
      return
    }
    if (wantsPanicPin && !/^\d{4,12}$/.test(panicPin)) {
      setStatus('error: panic PIN must be 4 to 12 digits')
      return
    }
    if (panicPinMismatch) {
      setStatus('error: panic PINs do not match')
      return
    }
    if (panicSameAsPin) {
      setStatus('error: panic PIN must be different from voting PIN')
      return
    }
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
        pin,
        panic_pin: wantsPanicPin ? panicPin : null,
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

      setRegistered(true)
      setStep(4)
      setStatus(data.message || 'success')

    } catch (err) {
      console.error('Registration error:', err)
      setStatus('error: ' + err.message)
      setStep(0)
    }
  }

  const STEPS = ['Roll No. + PIN', 'Server Challenge', 'Touch ID Scan', 'Confirmed']

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

          <label style={{
            display: 'block',
            fontSize: 11,
            letterSpacing: 2,
            color: '#667788',
            fontFamily: 'monospace',
            marginBottom: 8
          }}>
            CREATE VOTING PIN
          </label>
          <input
            value={pin}
            onChange={e => setPin(e.target.value.replace(/\D/g, '').slice(0, 12))}
            placeholder="4 to 12 digits"
            type="password"
            inputMode="numeric"
            autoComplete="off"
            data-lpignore="true"
            style={{
              width: '100%',
              padding: '14px 16px',
              border: '1px solid #ddd',
              borderBottom: '2px solid #0d1b2a',
              background: '#fafafa',
              fontSize: 16,
              fontFamily: 'monospace',
              outline: 'none',
              boxSizing: 'border-box',
              marginBottom: 24
            }}
          />

          <label style={{
            display: 'block',
            fontSize: 11,
            letterSpacing: 2,
            color: '#667788',
            fontFamily: 'monospace',
            marginBottom: 8
          }}>
            CONFIRM PIN
          </label>
          <input
            value={confirmPin}
            onChange={e => setConfirmPin(e.target.value.replace(/\D/g, '').slice(0, 12))}
            placeholder="Re-enter your PIN"
            type="password"
            inputMode="numeric"
            autoComplete="off"
            data-lpignore="true"
            style={{
              width: '100%',
              padding: '14px 16px',
              border: '1px solid #ddd',
              borderBottom: '2px solid #0d1b2a',
              background: '#fafafa',
              fontSize: 16,
              fontFamily: 'monospace',
              outline: 'none',
              boxSizing: 'border-box',
              marginBottom: 32
            }}
          />
          {pinMismatch && (
            <div style={{ marginTop: -20, marginBottom: 24, color: '#8a1a1a', fontFamily: 'monospace', fontSize: 11 }}>
              PINs do not match.
            </div>
          )}

          <div style={{
            marginTop: 8,
            paddingTop: 24,
            borderTop: '1px solid #eee'
          }}>
            <div style={{ fontSize: 11, letterSpacing: 2, color: '#667788', fontFamily: 'monospace', marginBottom: 8 }}>
              OPTIONAL PANIC PIN
            </div>
            <p style={{ color: '#667788', fontSize: 12, lineHeight: 1.6, margin: '0 0 16px' }}>
              Set this only if you want a duress PIN. It will accept the vote normally on screen,
              but the ballot is excluded from final results.
            </p>

            <input
              value={panicPin}
              onChange={e => setPanicPin(e.target.value.replace(/\D/g, '').slice(0, 12))}
              placeholder="Optional 4 to 12 digits"
              type="password"
              inputMode="numeric"
              autoComplete="off"
              data-lpignore="true"
              style={{
                width: '100%',
                padding: '14px 16px',
                border: '1px solid #ddd',
                borderBottom: panicPin ? '2px solid #0d1b2a' : '2px solid #ddd',
                background: '#fafafa',
                fontSize: 16,
                fontFamily: 'monospace',
                outline: 'none',
                boxSizing: 'border-box',
                marginBottom: 16
              }}
            />

            <input
              value={confirmPanicPin}
              onChange={e => setConfirmPanicPin(e.target.value.replace(/\D/g, '').slice(0, 12))}
              placeholder="Confirm optional panic PIN"
              type="password"
              inputMode="numeric"
              autoComplete="off"
              data-lpignore="true"
              style={{
                width: '100%',
                padding: '14px 16px',
                border: '1px solid #ddd',
                borderBottom: confirmPanicPin ? '2px solid #0d1b2a' : '2px solid #ddd',
                background: '#fafafa',
                fontSize: 16,
                fontFamily: 'monospace',
                outline: 'none',
                boxSizing: 'border-box',
                marginBottom: 32
              }}
            />
            {panicPinMismatch && (
              <div style={{ marginTop: -20, marginBottom: 24, color: '#8a1a1a', fontFamily: 'monospace', fontSize: 11 }}>
                Panic PINs do not match.
              </div>
            )}
            {panicSameAsPin && (
              <div style={{ marginTop: -20, marginBottom: 24, color: '#8a1a1a', fontFamily: 'monospace', fontSize: 11 }}>
                Panic PIN must be different from your voting PIN.
              </div>
            )}
          </div>

          <button
            onClick={handleRegister}
            disabled={!rollNo || !pin || !confirmPin || pinMismatch || panicPinMismatch || panicSameAsPin || step > 0}
            style={{
              width: '100%',
              padding: '16px',
              background: !rollNo || !pin || !confirmPin || pinMismatch || panicPinMismatch || panicSameAsPin || step > 0 ? '#ddd' : '#0d1b2a',
              color: !rollNo || !pin || !confirmPin || pinMismatch || panicPinMismatch || panicSameAsPin || step > 0 ? '#aaa' : 'white',
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

        {registered && (
          <div style={{
            marginTop: 2,
            background: '#0d1b2a',
            padding: 32,
            borderLeft: '3px solid #c8a951'
          }}>
            <div style={{ color: '#c8a951', fontSize: 11, letterSpacing: 2, fontFamily: 'monospace', marginBottom: 12 }}>
              ✓ REGISTRATION COMPLETE
            </div>
            <div style={{ color: 'white', fontSize: 24, fontWeight: 700, marginBottom: 8 }}>
              Your PIN is active.
            </div>
            <p style={{ color: '#667788', fontSize: 12, marginTop: 16, lineHeight: 1.6 }}>
              Use this PIN with Touch ID when casting your vote. You will also use it with
              your Ballot ID to verify your receipt later. The server stores only a hash.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
