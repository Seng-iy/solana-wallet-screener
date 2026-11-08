import asyncio
import json
import requests
import websockets

# ==========================================
# CONFIGURATION
# ==========================================
HELIUS_API_KEY = "YOUR_HELIUS_API_KEY_HERE"
WSS_ENDPOINT = f"wss://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"

# Paste your Telegram credentials here
TELEGRAM_BOT_TOKEN = "9219473756:AAELR3Sg5yO85DH7skcqZWzXZDDT5ZoHdl0"
TELEGRAM_CHAT_ID = "6870233188"

TARGET_WALLET = "8xiSugaCSFAMd1Cfosz82wiUKvHDmzKYPTjE4sAVaftH"

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def send_telegram_alert(wallet, signature, slot):
    """Pushes a verified wallet transaction alert to your Telegram chat."""
    message = (
        f"🎯 <b>TARGET WALLET ACTIVITY DETECTED</b>\n\n"
        f"<b>Wallet:</b> <code>{wallet}</code>\n"
        f"<b>Slot:</b> {slot}\n"
        f"<b>Tx Signature:</b> <code>{signature}</code>\n\n"
        f"🔗 <a href='https://solscan.io/tx/{signature}'>View on Solscan</a>"
    )
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")

# ==========================================
# ASYNC WEBSOCKET LISTENER WITH FILTERS
# ==========================================
async def monitor_solana_wallet():
    print(f"🚀 Connecting to Helius Solana RPC...")
    
    async with websockets.connect(WSS_ENDPOINT) as socket:
        print(f"✅ Connected! Subscribing to wallet activity for: {TARGET_WALLET}\n")
        
        subscription_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "logsSubscribe",
            "params": [
                {"mentions": [TARGET_WALLET]},
                {"commitment": "confirmed"}
            ]
        }
        
        await socket.send(json.dumps(subscription_request))

        while True:
            try:
                response = await socket.recv()
                data = json.loads(response)

                if "result" in data:
                    print(f"Subscribed successfully. Subscription ID: {data['result']}")
                    continue

                if "params" in data and "result" in data["params"]:
                    value = data["params"]["result"]["value"]
                    signature = value.get("signature")
                    slot = data["params"]["result"]["context"].get("slot")
                    err = value.get("err")

                    # --- FILTER LOGIC ---
                    # Only process if transaction succeeded (err is None)
                    if not err and signature:
                        print(f"⚡ [FILTERED TRADE] Slot: {slot} | Signature: {signature}")
                        
                        # Trigger Telegram notification
                        send_telegram_alert(TARGET_WALLET, signature, slot)

            except websockets.exceptions.ConnectionClosed:
                print("❌ Connection dropped. Reconnecting loops...")
                break
            except Exception as e:
                print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(monitor_solana_wallet())