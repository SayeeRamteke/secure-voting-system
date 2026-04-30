# 🔐 Secure Voting System using Cryptographic Security Mechanisms

A modern, privacy-preserving, and tamper-evident electronic voting system built using strong cryptographic primitives and hardware-backed authentication.

---

## 🚀 Overview

This project implements a **secure end-to-end electronic voting platform** that eliminates blind trust in centralized systems by replacing it with **cryptographic guarantees**.

It ensures:

* **Confidentiality** → No one can read votes before tally
* **Integrity** → Any tampering is detectable
* **Authentication** → Only legitimate voters can vote
* **Anonymity** → Votes cannot be linked to identities
* **Fairness** → One person, one vote

---

## 🧠 Key Idea

> Don’t trust the server. Verify everything cryptographically.

Instead of relying on administrators or databases, this system enforces security using:

* encryption
* hashing
* digital signatures
* distributed key control

---

## 🏆 Core Strengths

### 🔒 1. Zero-Trust Architecture

* Server never sees plaintext votes
* No single authority can decrypt votes independently

---

### 🔑 2. Hybrid Encryption Model

* Vote encrypted using AES-256-GCM
* AES key protected using X25519 key exchange
* Ensures both **performance and strong security**

---

### 🧬 3. Hardware-Backed Authentication

* Built on WebAuthn (FIDO2)
* Private keys stored in Secure Enclave / TPM
* Resistant to phishing and credential theft

---

### 🌳 4. Tamper Detection via Merkle Trees

* Every vote becomes part of a cryptographic tree
* Any modification → changes root hash → instantly detectable

---

### 🧾 5. End-to-End Verifiability

* Voters receive proof of inclusion
* Anyone can independently verify election integrity

---

### 🧑‍⚖️ 6. Threshold Cryptography (No Single Point of Failure)

* Election private key split using Shamir Secret Sharing
* Requires multiple trustees to decrypt votes

---

### 🎭 7. Coercion Resistance (Panic PIN)

* Fake vote can be cast under pressure
* System behaves normally, but excludes it during tally

---

### 🔁 8. Forward Secrecy per Vote

* Each vote uses a unique ephemeral key
* Compromise of one vote does NOT affect others

---

## 🏗️ System Architecture

### 📌 Phase 1: Voter Registration

* User registers with roll number + PIN
* WebAuthn generates hardware key pair
* Public key stored, private key never leaves device

---

### 📌 Phase 2: Vote Casting (Client-Side Secure Pipeline)

1. Vote selected
2. Encrypted using AES-256-GCM
3. AES key wrapped using X25519
4. Nullifier generated (prevents double voting)
5. Entire payload signed via WebAuthn

---

### 📌 Phase 3: Server Verification

* Signature verification (authentic voter)
* Nullifier uniqueness check (no duplicate voting)
* Panic PIN detection (decoy vote)
* Vote stored + added to Merkle Tree

---

### 📌 Phase 4: Tamper Monitoring

* Continuous Merkle root recomputation
* Any database manipulation triggers mismatch

---

### 📌 Phase 5: Secure Tally

* Trustees submit key shares
* Shamir reconstruction of private key
* Votes decrypted
* Decoy votes excluded

---

## 🛠️ Tech Stack

### Backend

* Python 3
* FastAPI

### Frontend

* React

### Database

* SQLite (prototype)

### Cryptography

* AES-256-GCM (encryption)
* X25519 (key exchange)
* Ed25519 (signatures)
* BLAKE3 (hashing)
* HKDF (key derivation)
* Shamir Secret Sharing (threshold security)

---

## 🔐 Security Properties Achieved

| Property         | Mechanism Used           |
| ---------------- | ------------------------ |
| Confidentiality  | AES-256 + X25519         |
| Integrity        | BLAKE3 + Merkle Tree     |
| Authentication   | WebAuthn (hardware keys) |
| Non-repudiation  | Digital signatures       |
| Anonymity        | Nullifier mechanism      |
| Tamper Detection | Merkle root verification |
| Decentralization | Threshold cryptography   |

---

## ⚠️ Known Limitations

This system is designed with strong security guarantees, but like all remote voting systems, some limitations remain:

* **Client-side malware risk** (vote can be altered before encryption)
* **Single-server bulletin board** (needs decentralization)
* **Key exposure window during tally**
* **No fully independent audit network yet**

---

## 🚀 Future Improvements

* 🔐 Zero-Knowledge Proofs for vote correctness
* 🌐 Distributed public bulletin board
* 🔄 Re-voting support for coercion resistance
* 📱 Independent verification channel (2nd device)
* ☁️ Cloud + scalable database architecture
* 🧠 Hardware-derived secrets (replace PIN-based nullifier)
* 🛡️ Secure voting environment (kiosk mode / dedicated app)

---

## 🎯 Why This Project Stands Out

Unlike traditional systems:

| Traditional Systems | This System             |
| ------------------- | ----------------------- |
| Trust admins        | Trust math              |
| Plain DB storage    | Encrypted votes         |
| No verification     | Merkle proofs           |
| Centralized keys    | Threshold keys          |
| Weak auth           | Hardware authentication |

---

## 📊 Use Cases

* College / University elections
* Secure organizational voting
* Governance platforms
* Integrity-critical surveys

---

## 🤝 Contributors

* Prachi Gengje
* Sayee Ramteke

---

## 📄 License

This project is for academic and research purposes.

---

