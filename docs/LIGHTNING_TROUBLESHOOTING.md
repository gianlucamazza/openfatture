# Lightning Network Troubleshooting Guide

This guide helps diagnose and resolve common issues with OpenFatture's Lightning Network integration.

---

## Quick Diagnosis

### Health Check Command

Run this first when encountering issues:

```bash
# Check overall Lightning status
openfatture lightning status

# Expected healthy output:
✅ LND Connection: OK (alias: MyNode)
📊 Channels: 3 active, 2.5M sats capacity
💰 Balance: 1.2M sats local, 800k sats remote
⚡ Rate: 45,000 EUR/BTC (CoinGecko, 2m ago)
🔄 Liquidity: OK (target: 50%, current: 48%)
```

### Configuration Validation

```bash
# Check Lightning configuration
openfatture config get | grep LIGHTNING

# Verify LND connectivity
lncli getinfo
```

---

## Connection Issues

### ❌ "Failed to connect to LND"

**Symptoms:**
- `openfatture lightning status` shows connection error
- All Lightning commands fail
- LND logs show no connection attempts

**Possible Causes & Solutions:**

#### 1. LND Not Running

```bash
# Check if LND is running
ps aux | grep lnd

# Start LND if not running
lnd

# Or check systemd status
sudo systemctl status lnd
```

#### 2. Wrong Host/Port

```bash
# Check configured host
openfatture config get lightning_host

# Test connection to LND gRPC
telnet localhost 10009

# Update configuration if needed
openfatture config set lightning_host localhost:10009
```

#### 3. Firewall Blocking

```bash
# Check firewall rules
sudo ufw status

# Allow LND gRPC port
sudo ufw allow 10009/tcp

# For remote LND, ensure VPN or secure tunnel
```

#### 4. Certificate Issues

```bash
# Check certificate file exists and is readable
ls -la ~/.lnd/tls.cert

# Verify certificate is not expired
openssl x509 -in ~/.lnd/tls.cert -text -noout | grep "Not After"

# Regenerate certificate if needed
lncli unlock  # If wallet is locked
```

### ❌ "Macaroon authentication failed"

**Symptoms:**
- Connection succeeds but authentication fails
- Error: `UNAUTHENTICATED`

**Solutions:**

#### Check Macaroon Path

```bash
# Verify macaroon file exists
ls -la ~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon

# Check file permissions (should be readable by OpenFatture user)
ls -l ~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon
```

#### Regenerate Macaroon

```bash
# Create new admin macaroon
lncli bakemacaroon \
  --save_to=~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon \
  uri:/lnrpc.Lightning/ListChannels \
  uri:/lnrpc.Lightning/SendPayment \
  uri:/lnrpc.Lightning/AddInvoice \
  uri:/lnrpc.Lightning/SubscribeInvoices

# Update OpenFatture configuration
openfatture config set lightning_macaroon_path ~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon
```

#### Check Macaroon Permissions

If you get permission errors, the macaroon might not have required permissions:

```bash
# Decode macaroon to check permissions (requires macaroon package)
python3 -c "
import base64
with open('~/.lnd/data/chain/bitcoin/mainnet/admin.macaroon', 'rb') as f:
    macaroon = f.read()
print('Macaroon permissions would be listed here')
"
```

### ❌ "Circuit breaker is open"

**Symptoms:**
- Commands fail with circuit breaker error
- Temporary unavailability after repeated failures

**Solutions:**

#### Wait for Recovery

```bash
# Circuit breaker automatically resets after timeout
# Default timeout: 5 minutes
openfatture config get lightning_circuit_breaker_timeout
```

#### Check LND Status

```bash
# Verify LND is responding
lncli getinfo

# Check LND logs for errors
tail -f ~/.lnd/logs/bitcoin/mainnet/lnd.log
```

#### Reset Circuit Breaker

Restart OpenFatture to reset circuit breaker state:

```bash
# Restart the application
# Circuit breaker state is not persisted
```

---

## Invoice Issues

### ❌ "Invoice creation failed"

**Symptoms:**
- `openfatture lightning invoice create` fails
- Error messages about amount or expiry

**Possible Causes:**

#### Invalid Amount

```bash
# Check amount is positive and reasonable
openfatture lightning invoice create --amount 100.00 --description "Test"

# Minimum amount: 0.01 EUR (very small)
# Maximum amount: Limited by channel capacity
```

#### Invalid Expiry Time

```bash
# Check expiry is within limits
openfatture config get lightning_min_expiry_hours  # Default: 1
openfatture config get lightning_max_expiry_hours  # Default: 168 (1 week)

# Valid example
openfatture lightning invoice create --amount 100.00 --expiry-hours 24 --description "Test"
```

#### Channel Capacity Issues

```bash
# Check available inbound capacity
openfatture lightning channels

# Need at least some inbound channels
lncli listchannels | jq '.channels[] | select(.active == true) | .remote_balance'
```

### ❌ "Invoice expired before payment"

**Symptoms:**
- Invoice shows as expired
- Payment attempts fail

**Solutions:**

#### Increase Default Expiry

```bash
# Set longer default expiry
openfatture config set lightning_default_expiry_hours 72  # 3 days

# Or specify expiry per invoice
openfatture lightning invoice create --amount 100.00 --expiry-hours 168 --description "Long expiry"
```

#### Check Invoice Status

```bash
# Monitor invoice status
openfatture lightning invoice status <invoice_id>

# Cancel expired invoices
openfatture lightning invoice cancel <invoice_id>
```

---

## Payment Issues

### ❌ "Payment not settling"

**Symptoms:**
- Invoice shows as open after payment attempt
- Payment stuck in "in_flight" status

**Possible Causes:**

#### Routing Issues

```bash
# Check channel connectivity
lncli describegraph | jq '.nodes | length'  # Should be > 1000

# Test small payment first
openfatture lightning invoice create --amount 0.01 --description "Test routing"
```

#### Insufficient Liquidity

```bash
# Check local channel balances
openfatture lightning channels

# Need outbound liquidity for payments
# Open more channels or wait for rebalancing
```

#### LND Sync Issues

```bash
# Check if LND is synced
lncli getinfo | jq '.synced_to_chain'

# Wait for sync to complete
tail -f ~/.lnd/logs/bitcoin/mainnet/lnd.log | grep "Caught up to chain"
```

### ❌ "Rate conversion failed"

**Symptoms:**
- Invoice creation fails with rate error
- BTC/EUR conversion unavailable

**Solutions:**

#### Check Rate Providers

```bash
# Test CoinGecko API
curl "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=eur"

# Test CoinMarketCap API (if configured)
curl "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=BTC&convert=EUR" \
  -H "X-CMC_PRO_API_KEY: YOUR_API_KEY"
```

#### Use Fallback Rate

```bash
# Set fallback rate when providers fail
openfatture config set lightning_fallback_rate 45000.00

# Disable problematic providers
openfatture config set lightning_coingecko_enabled false
openfatture config set lightning_cmc_enabled true
```

#### API Key Issues

```bash
# Verify API keys are set correctly
openfatture config get lightning_coingecko_api_key
openfatture config get lightning_cmc_api_key

# CoinMarketCap requires API key when enabled
openfatture config set lightning_cmc_api_key YOUR_API_KEY
```

---

## Liquidity Issues

### ❌ "No inbound liquidity"

**Symptoms:**
- Cannot receive payments
- All channels show 0% inbound ratio

**Solutions:**

#### Open Channels

```bash
# Find peers with inbound liquidity
lncli listpeers

# Open channel with peer
lncli openchannel --node_key=<peer_pubkey> --local_amt=500000 --push_amt=250000

# Use Lightning Network explorers to find peers
# https://1ml.com/
# https://explorer.acinq.co/
```

#### Channel Rebalancing

```bash
# Enable automatic liquidity management
openfatture config set lightning_liquidity_enabled true

# Or manual rebalancing (requires outbound liquidity)
lncli sendpayment --pay_req=<invoice> --fee_limit=1000
```

#### Use External Services

- **Lightning Pool**: https://lightning.engineering/pool/
- **Lightning Labs**: Channel opening services
- **Local liquidity providers**

### ❌ "Liquidity ratio too high/low"

**Symptoms:**
- Warnings about liquidity ratios
- Automatic rebalancing failing

**Solutions:**

#### Adjust Ratios

```bash
# Set appropriate liquidity targets
openfatture config set lightning_liquidity_min_ratio 0.2   # 20%
openfatture config set lightning_liquidity_target_ratio 0.5 # 50%
openfatture config set lightning_liquidity_max_ratio 0.8   # 80%
```

#### Manual Rebalancing

```bash
# Create invoice to receive funds
openfatture lightning invoice create --amount 50.00 --description "Rebalancing"

# Or use external rebalancing services
# https://lightningconductor.net/
```

---

## Webhook Issues

### ❌ "Webhook not receiving notifications"

**Symptoms:**
- Payments settle but no webhook calls
- Webhook endpoint not receiving data

**Solutions:**

#### Check Configuration

```bash
# Verify webhook settings
openfatture config get lightning_webhook_enabled
openfatture config get lightning_webhook_url
openfatture config get lightning_webhook_secret
```

#### Test Webhook Endpoint

```bash
# Test your endpoint manually
curl -X POST https://your-app.com/webhooks/lightning \
  -H "Content-Type: application/json" \
  -H "X-Lightning-Signature: test" \
  -d '{"event": "test", "timestamp": "'$(date -Iseconds)'"}'
```

#### Check Logs

```bash
# Check OpenFatture logs for webhook attempts
tail -f ~/.openfatture/logs/openfatture.log | grep webhook

# Look for webhook delivery errors
```

### ❌ "Invalid webhook signature"

**Symptoms:**
- Webhook requests rejected due to signature verification

**Solutions:**

#### Verify Secret

```bash
# Check webhook secret matches
openfatture config get lightning_webhook_secret

# Ensure secret is consistent between OpenFatture and your application
```

#### Debug Signature

```python
# Test signature generation
import hmac
import hashlib
import json

secret = "your_webhook_secret"
payload = {"event": "test", "amount": 100}
message = json.dumps(payload, sort_keys=True)
signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
print(f"Expected signature: {signature}")
```

---

## Performance Issues

### ❌ "Slow invoice creation"

**Symptoms:**
- Invoice creation takes > 5 seconds
- Rate provider timeouts

**Solutions:**

#### Optimize Timeouts

```bash
# Reduce gRPC timeout for faster failures
openfatture config set lightning_timeout_seconds 10

# Increase rate cache TTL
openfatture config set lightning_rate_cache_ttl 600  # 10 minutes
```

#### Use Local Rate Cache

```bash
# Enable more aggressive caching
openfatture config set lightning_rate_cache_ttl 1800  # 30 minutes
```

### ❌ "High memory usage"

**Symptoms:**
- OpenFatture using excessive memory
- Performance degradation over time

**Solutions:**

#### Adjust Cache Settings

```bash
# Reduce cache TTL
openfatture config set lightning_rate_cache_ttl 180  # 3 minutes

# Clear caches periodically
# Restart OpenFatture to clear in-memory caches
```

#### Monitor Resources

```bash
# Check memory usage
ps aux | grep openfatture

# Monitor LND resource usage
lncli getinfo | jq '.num_peers, .num_channels'
```

---

## Database Issues

### ❌ "Lightning data not persisting"

**Symptoms:**
- Invoices/payments not saved to database
- Data lost after restart

**Solutions:**

#### Check Database Connection

```bash
# Test database connectivity
python -c "
from openfatture.storage.database.session import get_session
session = next(get_session())
print('✅ Database OK')
"
```

#### Verify Migrations

```bash
# Check for pending migrations
alembic current

# Run migrations if needed
alembic upgrade head
```

#### Check Permissions

```bash
# Ensure database user has write permissions
# Check database logs for errors
```

---

## Advanced Troubleshooting

### Debug Logging

Enable detailed logging for diagnostics:

```bash
# Enable debug logging
openfatture config set ai_log_level DEBUG

# Check logs
tail -f ~/.openfatture/logs/openfatture.log
```

### LND Debug Commands

```bash
# Check LND status
lncli getinfo

# List active channels
lncli listchannels

# Check pending channels
lncli pendingchannels

# View recent payments
lncli listpayments --max_payments=10

# Check invoices
lncli listinvoices --max_invoices=10
```

### Network Diagnostics

```bash
# Test Bitcoin network connectivity
lncli getnetworkinfo

# Check peer connections
lncli listpeers

# Test payment routing
lncli queryroutes <destination> <amount>
```

### Reset Procedures

#### Soft Reset

```bash
# Restart OpenFatture
# This clears in-memory caches and circuit breaker state
```

#### Hard Reset

```bash
# Stop LND
lncli stop

# Backup important data
cp ~/.lnd/data/chain/bitcoin/mainnet/channel.db /backup/

# Restart LND
lnd

# Reconnect OpenFatture
openfatture lightning status
```

---

## Common Error Messages

### "invoice expired"

**Cause:** Invoice expiry time reached before payment
**Solution:** Create new invoice with longer expiry

### "insufficient local balance"

**Cause:** Not enough outbound liquidity for payment
**Solution:** Add funds to channels or open new channels

### "unable to find a path to destination"

**Cause:** No route available to destination
**Solution:** Wait for better connectivity or use on-chain payment

### "payment attempt timeout"

**Cause:** Payment stuck in transit
**Solution:** Increase fee limit or try different route

### "channel is disabled"

**Cause:** Channel temporarily disabled due to issues
**Solution:** Wait for channel to recover or use different channel

---

## Getting Help

### Community Resources

- **Lightning Network Community**: https://lightning.community/
- **LND Documentation**: https://docs.lightning.engineering/
- **Stack Exchange**: https://bitcoin.stackexchange.com/questions/tagged/lightning-network
- **Reddit**: r/lightningnetwork, r/LightningNetwork

### Professional Support

For enterprise deployments:
- Lightning node hosting providers
- Integration consultants
- 24/7 monitoring services

### Reporting Issues

When reporting issues, include:

```bash
# System information
openfatture --version
uname -a

# Configuration (redact secrets)
openfatture config get | grep -v password | grep -v secret | grep -v key

# Error logs
tail -50 ~/.openfatture/logs/openfatture.log

# LND information
lncli getinfo
lncli listchannels | jq '.channels | length'
```

---

## Prevention Best Practices

### Regular Maintenance

1. **Monitor channel health daily**
   ```bash
   openfatture lightning status
   ```

2. **Backup LND data weekly**
   ```bash
   cp ~/.lnd/data/chain/bitcoin/mainnet/channel.db /backup/
   ```

3. **Update LND regularly**
   ```bash
   # Check for updates
   lncli version
   ```

4. **Monitor Bitcoin node sync**
   ```bash
   lncli getinfo | jq '.synced_to_chain'
   ```

### Proactive Monitoring

1. **Set up alerts for:**
   - Channel force closes
   - Low liquidity warnings
   - Failed payment streaks
   - Rate provider failures

2. **Monitor key metrics:**
   - Channel capacity and balance
   - Payment success rate
   - Invoice settlement time
   - Webhook delivery success

### Capacity Planning

1. **Calculate required liquidity:**
   - Estimate monthly invoice volume
   - Add 20-50% buffer for fluctuations
   - Plan for seasonal variations

2. **Diversify channels:**
   - Connect to multiple peers
   - Use different channel sizes
   - Maintain geographic diversity

---

*Last updated: January 2025*
