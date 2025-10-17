# Lightning Network Integration

OpenFatture integrates with the Lightning Network to enable instant, low-fee Bitcoin payments for your invoices. This guide covers setup, configuration, and usage workflows.

---

## Overview

The Lightning Network is a layer-2 scaling solution for Bitcoin that enables:
- ⚡ **Instant payments** - Settle in seconds instead of hours
- 💰 **Low fees** - Typically 0.1-1 EUR per transaction
- 🌍 **Global reach** - Pay anyone with a Lightning wallet
- 🔒 **Secure** - Built on Bitcoin's security model

### Key Features

- **Invoice Generation**: Create Lightning invoices from existing invoices
- **Payment Tracking**: Monitor payment status in real-time
- **Webhook Notifications**: Get instant payment confirmations
- **Liquidity Management**: Automatic channel balancing (optional)
- **Multi-Provider Rates**: BTC/EUR conversion from CoinGecko and CoinMarketCap
- **Circuit Breaker**: Automatic failure handling and recovery

---

## Prerequisites

### 1. LND Node

You need a running Lightning Network Daemon (LND) node:

**Option A: Run your own LND node**
```bash
# Install LND (Ubuntu/Debian)
sudo apt update
sudo apt install lnd

# Or download from https://github.com/lightningnetwork/lnd/releases

# Start LND
lnd
```

**Option B: Use a hosted Lightning service**
- Voltage.cloud
- Lightning Labs
- Other LND-compatible providers

### 2. Channel Funding

Your LND node needs inbound liquidity (channels) to receive payments:

```bash
# Check current channels
lncli listchannels

# Open a channel (example: 1M sats = ~45 EUR at 45k EUR/BTC)
lncli openchannel --node_key=<peer_pubkey> --local_amt=1000000 --push_amt=0
```

**Recommended minimum**: 500,000 sats (~22 EUR) inbound capacity

### 3. Firewall Configuration

Ensure LND's gRPC port (10009) is accessible:

```bash
# Allow LND gRPC port
sudo ufw allow 10009/tcp

# Or configure your cloud firewall
```

---

## Quick Start

### 1. Enable Lightning

```bash
# Enable Lightning integration
openfatture config set lightning_enabled true

# Set LND connection details
openfatture config set lightning_host localhost:10009
openfatture config set lightning_cert_path ~/.lnd/tls.cert
openfatture config set lightning_macaroon_path ~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon
```

### 2. Test Connection

```bash
# Test LND connectivity
openfatture lightning status

# Expected output:
# ✅ LND Connection: OK
# 📊 Channels: 3 active, 2.5M sats capacity
# 💰 Balance: 1.2M sats local, 800k sats remote
```

### 3. Create Your First Lightning Invoice

```bash
# Create invoice from existing invoice
openfatture lightning invoice create --numero INV-001 --amount 500.00

# Output:
# ⚡ Lightning Invoice Created
# 📄 Invoice: INV-001-LN
# 💰 Amount: 500.00 EUR (11,111 sats @ 45,000 EUR/BTC)
# ⏰ Expires: 2025-01-15 10:30:00
# 🔗 Payment Request: lnbc111110n1...
```

### 4. Check Payment Status

```bash
# Monitor payment
openfatture lightning status

# Or check specific invoice
openfatture lightning invoice status INV-001-LN
```

---

## Configuration

### Basic Setup

```env
# Enable Lightning
LIGHTNING_ENABLED=true

# LND Connection
LIGHTNING_HOST=localhost:10009
LIGHTNING_CERT_PATH=~/.lnd/tls.cert
LIGHTNING_MACAROON_PATH=~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon

# Invoice Settings
LIGHTNING_DEFAULT_EXPIRY_HOURS=24
LIGHTNING_MIN_EXPIRY_HOURS=1
LIGHTNING_MAX_EXPIRY_HOURS=168
```

### Advanced Configuration

```env
# BTC Rate Providers
LIGHTNING_COINGECKO_ENABLED=true
LIGHTNING_COINGECKO_API_KEY=your_api_key
LIGHTNING_CMC_ENABLED=false
LIGHTNING_FALLBACK_RATE=45000.00
LIGHTNING_RATE_CACHE_TTL=300

# Reliability
LIGHTNING_TIMEOUT_SECONDS=30
LIGHTNING_MAX_RETRIES=3
LIGHTNING_CIRCUIT_BREAKER_FAILURES=5
LIGHTNING_CIRCUIT_BREAKER_TIMEOUT=300

# Webhooks (optional)
LIGHTNING_WEBHOOK_ENABLED=true
LIGHTNING_WEBHOOK_URL=https://your-app.com/webhooks/lightning
LIGHTNING_WEBHOOK_SECRET=your_secret
```

See [Configuration Reference](../docs/CONFIGURATION.md#lightning-network-configuration) for all options.

---

## Usage Workflows

### Creating Lightning Invoices

#### From Existing Invoice

```bash
# Create Lightning invoice from existing invoice
openfatture lightning invoice create --numero INV-001

# With custom amount
openfatture lightning invoice create --numero INV-001 --amount 250.00

# With custom expiry (hours)
openfatture lightning invoice create --numero INV-001 --expiry-hours 48
```

#### Standalone Lightning Invoice

```bash
# Create standalone Lightning invoice
openfatture lightning invoice create --amount 100.00 --description "Consulting services"

# With custom expiry
openfatture lightning invoice create --amount 100.00 --description "Consulting" --expiry-hours 72
```

### Managing Invoices

```bash
# List all Lightning invoices
openfatture lightning invoice list

# Check specific invoice status
openfatture lightning invoice status INV-001-LN

# Cancel unpaid invoice
openfatture lightning invoice cancel INV-001-LN
```

### Channel Management

```bash
# View channel status
openfatture lightning channels

# Check liquidity ratios
openfatture lightning liquidity status

# Enable automatic liquidity management
openfatture config set lightning_liquidity_enabled true
openfatture config set lightning_liquidity_min_ratio 0.2
openfatture config set lightning_liquidity_target_ratio 0.5
```

### Payment Monitoring

```bash
# Real-time payment status
openfatture lightning status

# View payment history
openfatture lightning payments list

# Get payment details
openfatture lightning payments show <payment_hash>
```

---

## Web UI Integration

### Lightning Dashboard

Access the Lightning dashboard at: **http://localhost:8501** → ⚡ Lightning

The dashboard shows:
- Connection status
- Channel overview
- Recent payments
- Liquidity metrics
- Configuration settings

### Invoice Generation

Use the web interface to:
- Generate Lightning invoices from existing invoices
- Monitor payment status
- View payment history
- Configure Lightning settings

---

## Webhook Integration

### Setup Webhooks

```env
LIGHTNING_WEBHOOK_ENABLED=true
LIGHTNING_WEBHOOK_URL=https://your-app.com/webhooks/lightning
LIGHTNING_WEBHOOK_SECRET=your_webhook_secret
```

### Webhook Payload

```json
{
  "event": "payment_received",
  "invoice_id": "INV-001-LN",
  "payment_hash": "a1b2c3d4...",
  "amount_sats": 11111,
  "amount_eur": 500.00,
  "timestamp": "2025-01-15T10:30:00Z",
  "description": "Invoice INV-001",
  "metadata": {
    "original_invoice": "INV-001",
    "client": "Acme Corp"
  }
}
```

### Webhook Events

- `payment_received` - Payment successfully settled
- `payment_failed` - Payment failed or expired
- `invoice_created` - New Lightning invoice generated
- `invoice_cancelled` - Invoice cancelled before payment

### Security

Webhooks include an `X-Lightning-Signature` header for verification:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)
```

---

## Troubleshooting

### Connection Issues

**Error: "Failed to connect to LND"**

```bash
# Check LND status
lncli getinfo

# Verify certificate path
ls -la ~/.lnd/tls.cert

# Test gRPC connection
grpcurl -cacert ~/.lnd/tls.cert -cert ~/.lnd/tls.cert -key ~/.lnd/tls.key localhost:10009 listchannels
```

**Error: "Macaroon authentication failed"**

```bash
# Check macaroon permissions
lncli bakemacaroon --help

# Regenerate admin macaroon
lncli bakemacaroon \
  --save_to=~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon \
  uri:/lnrpc.Lightning/ListChannels \
  uri:/lnrpc.Lightning/SendPayment \
  uri:/lnrpc.Lightning/AddInvoice
```

### Payment Issues

**Payments not settling**

```bash
# Check channel liquidity
openfatture lightning channels

# Verify invoice expiry
openfatture lightning invoice status <invoice_id>

# Check LND logs
tail -f ~/.lnd/logs/bitcoin/mainnet/lnd.log
```

**High fees or routing failures**

```bash
# Check channel fees
lncli listchannels | jq '.channels[].fee_per_milli'

# Update channel policies
lncli updatechanpolicy --base_fee_msat 1000 --fee_rate 0.0001 --time_lock_delta 40 --channel_point <chan_point>
```

### Rate Provider Issues

**BTC/EUR conversion failing**

```bash
# Test CoinGecko API
curl "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur"

# Check API key (if using)
openfatture config get lightning_coingecko_api_key

# Enable fallback rate
openfatture config set lightning_fallback_rate 45000.00
```

### Liquidity Problems

**No inbound capacity**

```bash
# Check current liquidity
openfatture lightning liquidity status

# Open new channels
lncli connect <peer_pubkey>@<peer_address>
lncli openchannel --node_key=<peer_pubkey> --local_amt=500000 --push_amt=250000

# Use channel opening services
# - https://lightningconductor.net/
# - https://lnmarkets.com/
```

---

## Best Practices

### Security

1. **Secure LND access**
   - Use firewall rules to restrict gRPC access
   - Rotate macaroons regularly
   - Never expose LND ports publicly

2. **Backup regularly**
   ```bash
   # Backup channel database
   cp ~/.lnd/data/chain/bitcoin/mainnet/channel.db /secure/backup/

   # Backup seed phrase (one-time)
   lncli getseed
   ```

3. **Monitor channels**
   - Watch for force closes
   - Monitor peer reliability
   - Keep channels balanced

### Operations

1. **Invoice expiry**
   - Use 24-48 hours for standard invoices
   - Extend for international payments
   - Monitor expiry times

2. **Fee management**
   - Set competitive channel fees
   - Monitor routing success rates
   - Adjust fees based on network conditions

3. **Liquidity management**
   - Maintain 20-50% inbound capacity
   - Use circular rebalancing when needed
   - Consider submarine swaps for large amounts

### Business Integration

1. **Client communication**
   - Inform clients about Lightning payment option
   - Provide clear payment instructions
   - Include QR codes in invoices

2. **Accounting**
   - Track Lightning fees separately
   - Record BTC/EUR conversion rates
   - Maintain payment confirmations

3. **Compliance**
   - Verify client identity for large payments
   - Report transactions if required
   - Keep detailed payment records

---

## Advanced Features

### Automatic Liquidity Management

Enable automatic channel rebalancing:

```env
LIGHTNING_LIQUIDITY_ENABLED=true
LIGHTNING_LIQUIDITY_MIN_RATIO=0.2
LIGHTNING_LIQUIDITY_TARGET_RATIO=0.5
LIGHTNING_LIQUIDITY_MAX_RATIO=0.8
LIGHTNING_LIQUIDITY_CHECK_INTERVAL=3600
```

### Multi-Provider Rate Conversion

Use multiple BTC price providers for reliability:

```env
LIGHTNING_COINGECKO_ENABLED=true
LIGHTNING_COINGECKO_API_KEY=your_key
LIGHTNING_CMC_ENABLED=true
LIGHTNING_CMC_API_KEY=your_key
LIGHTNING_FALLBACK_RATE=45000.00
```

### Custom Webhook Integration

Build custom integrations with webhook notifications:

```python
# Example webhook handler
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhooks/lightning', methods=['POST'])
def lightning_webhook():
    payload = request.get_data()
    signature = request.headers.get('X-Lightning-Signature')
    secret = 'your_webhook_secret'

    # Verify signature
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return jsonify({'error': 'Invalid signature'}), 401

    # Process payment
    data = request.get_json()
    if data['event'] == 'payment_received':
        # Update invoice status
        # Send confirmation email
        # Update accounting system
        pass

    return jsonify({'status': 'ok'})
```

---

## API Reference

### CLI Commands

```bash
# Core commands
openfatture lightning status                    # System status
openfatture lightning channels                  # Channel overview
openfatture lightning payments list             # Payment history

# Invoice management
openfatture lightning invoice create [options]  # Create invoice
openfatture lightning invoice list              # List invoices
openfatture lightning invoice status <id>       # Invoice status
openfatture lightning invoice cancel <id>       # Cancel invoice

# Liquidity management
openfatture lightning liquidity status          # Liquidity overview
openfatture lightning liquidity rebalance       # Manual rebalance
```

### Configuration Options

See [Configuration Reference](../docs/CONFIGURATION.md#lightning-network-configuration) for all settings.

---

## Support & Resources

### Community Resources

- [Lightning Network Documentation](https://docs.lightning.engineering/)
- [LND Documentation](https://docs.lightning.engineering/lightning-network-tools/lnd)
- [Lightning Network Explorer](https://explorer.acinq.co/)
- [1ML Lightning Statistics](https://1ml.com/)

### Getting Help

- Check [Troubleshooting](#troubleshooting) section
- Review LND logs: `tail -f ~/.lnd/logs/bitcoin/mainnet/lnd.log`
- Test with [Lightning Dev Kit](https://github.com/lightningdevkit)
- Join [Lightning Community](https://lightning.community/)

### Professional Services

For enterprise deployments:
- Lightning node hosting services
- Channel management services
- Integration consulting
- 24/7 monitoring and support

---

*Last updated: January 2025*
