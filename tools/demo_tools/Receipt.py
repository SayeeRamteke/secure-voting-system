import requests

BASE_URL = "http://localhost:8000"

leaf_index = input("Enter your leaf index (from your receipt): ").strip()
voter_secret = input("Enter your voter secret: ").strip()

print(f"\nVerifying vote at leaf #{leaf_index}...")

try:
    resp = requests.post(f"{BASE_URL}/receipt/verify", json={
        "leaf_index": int(leaf_index),
        "voter_secret": voter_secret
    })
    data = resp.json()

    print("\nMerkle Proof Path:")
    print("-" * 50)
    for i, step in enumerate(data.get("proof_path", [])):
        print(f"  Level {i+1}: {step['hash'][:32]}...  ✅")
    print("-" * 50)
    print(f"Root: {data.get('root_hash', 'N/A')[:32]}...")

    if data.get("verified"):
        print("\n✅ Your vote is INTACT and included in the tally.")
    else:
        print("\n❌ Verification FAILED.")

except Exception as e:
    print(f"Error: {e}")
    print("Make sure the backend server is running at localhost:8000")