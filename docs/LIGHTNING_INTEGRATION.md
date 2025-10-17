# Lightning Network Technical Integration

This document provides technical details about OpenFatture's Lightning Network integration, including architecture, LND connectivity, event handling, and webhook implementation.

---

## Architecture Overview

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Layer     │    │ Application Layer│    │  Domain Layer   │
│                 │    │                  │    │                 │
│ • lightning_cli │───▶│ • InvoiceService │───▶│ • Invoice       │
│ • lifespan.py   │    │ • PaymentService │    │ • Payment       │
│                 │    │ • LiquiditySvc   │    │ • Channel       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│Infrastructure   │    │   Event System   │    │   Web Layer     │
│                 │    │                  │    │                 │
│ • LND Client    │◀───│ • Event Handlers │───▶│ • Streamlit UI  │
│ • Repository    │    │ • Global Bus     │    │ • Webhooks      │
│ • Rate Provider │    │ • Async Events   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Key Design Patterns

- **Domain-Driven Design (DDD)**: Clear separation of domain, application, and infrastructure layers
- **Hexagonal Architecture**: Domain logic isolated from external dependencies
- **Event-Driven**: Asynchronous event handling for payment notifications
- **Circuit Breaker**: Fault tolerance for LND connection issues
- **Repository Pattern**: Data access abstraction

---

## LND Integration

### Connection Management

The LND client uses gRPC with TLS and macaroon authentication:

```python
# Connection configuration
@dataclass
class LNDConfig:
    host: str = "localhost:10009"
    cert_path: Path | None = None
    macaroon_path: Path | None = None
    timeout_seconds: int = 30
    max_retries: int = 3
```

### Authentication Flow

1. **TLS Certificate**: Validates server identity
2. **Macaroon**: Provides fine-grained permissions
3. **gRPC Metadata**: Attaches authentication headers

```python
# Macaroon loading and validation
def load_macaroon(self) -> bytes:
    with open(self.macaroon_path, 'rb') as f:
        return f.read()

# gRPC interceptor for authentication
class MacaroonInterceptor(grpc.UnaryUnaryClientInterceptor):
    def intercept_unary_unary(self, continuation, client_call_details, request):
        metadata = list(client_call_details.metadata)
        metadata.append(('macaroon', self.macaroon_b64))
        client_call_details = client_call_details._replace(metadata=metadata)
        return continuation(client_call_details, request)
```

### Circuit Breaker Implementation

Prevents cascading failures when LND is unavailable:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func: Callable, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenException()

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
```

### Error Handling

Comprehensive error mapping from LND to domain exceptions:

```python
class LNDErrorMapper:
    @staticmethod
    def map_error(rpc_error: grpc.RpcError) -> LNDException:
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            return LNDConnectionError("LND node is unavailable")
        elif rpc_error.code() == grpc.StatusCode.UNAUTHENTICATED:
            return LNDAuthenticationError("Invalid macaroon or certificate")
        elif rpc_error.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
            return LNDTimeoutError("Request timed out")
        # ... additional mappings
```

---

## Domain Model

### Core Entities

#### LightningInvoice

```python
@dataclass
class LightningInvoice:
    id: str
    amount_sats: int
    amount_eur: Decimal
    description: str
    payment_request: str
    payment_hash: str
    expiry_time: datetime
    status: InvoiceStatus
    created_at: datetime
    settled_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

#### Payment

```python
@dataclass
class Payment:
    payment_hash: str
    amount_sats: int
    amount_eur: Decimal
    fee_sats: int
    fee_eur: Decimal
    status: PaymentStatus
    created_at: datetime
    settled_at: datetime | None = None
    description: str | None = None
    invoice_id: str | None = None
```

#### Channel

```python
@dataclass
class Channel:
    channel_point: str
    capacity: int
    local_balance: int
    remote_balance: int
    active: bool
    private: bool
    initiator: bool
    chan_status_flags: str
    local_chan_reserve_sat: int
    remote_chan_reserve_sat: int
```

### Value Objects

#### BitcoinAmount

```python
@dataclass(frozen=True)
class BitcoinAmount:
    sats: int

    @property
    def btc(self) -> Decimal:
        return Decimal(self.sats) / 100_000_000

    @classmethod
    def from_btc(cls, btc: Decimal) -> 'BitcoinAmount':
        return cls(int(btc * 100_000_000))
```

#### EuroAmount

```python
@dataclass(frozen=True)
class EuroAmount:
    eur: Decimal

    @classmethod
    def from_sats(cls, sats: int, rate: Decimal) -> 'EuroAmount':
        btc = Decimal(sats) / 100_000_000
        return cls(btc * rate)
```

### Enums

```python
class InvoiceStatus(Enum):
    OPEN = "open"
    SETTLED = "settled"
    CANCELLED = "cancelled"
    ACCEPTED = "accepted"
    EXPIRED = "expired"

class PaymentStatus(Enum):
    IN_FLIGHT = "in_flight"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNKNOWN = "unknown"
```

---

## Application Services

### InvoiceService

Handles Lightning invoice lifecycle:

```python
class InvoiceService:
    def __init__(
        self,
        lnd_client: LNDClient,
        rate_provider: RateProvider,
        repository: LightningRepository,
        event_bus: EventBus
    ):
        self.lnd_client = lnd_client
        self.rate_provider = rate_provider
        self.repository = repository
        self.event_bus = event_bus

    async def create_invoice(
        self,
        amount_eur: Decimal,
        description: str,
        expiry_hours: int = 24,
        metadata: dict | None = None
    ) -> LightningInvoice:
        # Get current BTC/EUR rate
        rate = await self.rate_provider.get_rate()

        # Convert EUR to sats
        amount_sats = int((amount_eur / rate) * 100_000_000)

        # Create LND invoice
        lnd_invoice = await self.lnd_client.add_invoice(
            value_sats=amount_sats,
            memo=description,
            expiry_seconds=expiry_hours * 3600
        )

        # Create domain invoice
        invoice = LightningInvoice(
            id=lnd_invoice.payment_request[:16],  # Short ID
            amount_sats=amount_sats,
            amount_eur=amount_eur,
            description=description,
            payment_request=lnd_invoice.payment_request,
            payment_hash=lnd_invoice.payment_hash,
            expiry_time=datetime.now() + timedelta(hours=expiry_hours),
            status=InvoiceStatus.OPEN,
            created_at=datetime.now(),
            metadata=metadata or {}
        )

        # Persist and publish event
        await self.repository.save_invoice(invoice)
        await self.event_bus.publish(
            InvoiceCreatedEvent(invoice=invoice)
        )

        return invoice
```

### PaymentService

Manages payment monitoring and settlement:

```python
class PaymentService:
    async def monitor_payments(self) -> None:
        """Continuously monitor for new payments"""
        async for payment_update in self.lnd_client.subscribe_invoices():
            if payment_update.settled:
                # Get invoice details
                invoice = await self.repository.get_invoice_by_hash(
                    payment_update.payment_hash
                )

                if invoice:
                    # Update invoice status
                    invoice.status = InvoiceStatus.SETTLED
                    invoice.settled_at = datetime.now()
                    await self.repository.save_invoice(invoice)

                    # Create payment record
                    payment = Payment(
                        payment_hash=payment_update.payment_hash,
                        amount_sats=payment_update.amount_paid_sats,
                        amount_eur=invoice.amount_eur,
                        fee_sats=0,  # Receiver pays no fee
                        fee_eur=Decimal('0'),
                        status=PaymentStatus.SUCCEEDED,
                        created_at=datetime.now(),
                        settled_at=datetime.now(),
                        description=invoice.description,
                        invoice_id=invoice.id
                    )

                    await self.repository.save_payment(payment)

                    # Publish settlement event
                    await self.event_bus.publish(
                        PaymentReceivedEvent(
                            invoice=invoice,
                            payment=payment
                        )
                    )
```

### LiquidityService

Automatic channel liquidity management:

```python
class LiquidityService:
    async def check_and_rebalance(self) -> None:
        """Check liquidity ratios and rebalance if needed"""
        channels = await self.lnd_client.list_channels()

        for channel in channels:
            ratio = channel.local_balance / channel.capacity

            if ratio < self.min_ratio:
                # Need more inbound liquidity
                await self._rebalance_channel(channel, 'inbound')
            elif ratio > self.max_ratio:
                # Too much outbound liquidity
                await self._rebalance_channel(channel, 'outbound')

    async def _rebalance_channel(
        self,
        channel: Channel,
        direction: str
    ) -> None:
        # Find suitable peer channels for rebalancing
        # Execute circular payment to rebalance
        # Publish liquidity event
        pass
```

---

## Event System

### Event Types

```python
@dataclass
class InvoiceCreatedEvent:
    invoice: LightningInvoice
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PaymentReceivedEvent:
    invoice: LightningInvoice
    payment: Payment
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PaymentFailedEvent:
    payment_hash: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class LiquidityEvent:
    channel_point: str
    old_ratio: float
    new_ratio: float
    action: str
    timestamp: datetime = field(default_factory=datetime.now)
```

### Event Handlers

```python
class LightningEventHandlers:
    def __init__(self, repository: LightningRepository):
        self.repository = repository

    @event_handler(PaymentReceivedEvent)
    async def on_payment_received(self, event: PaymentReceivedEvent) -> None:
        # Update related invoice status
        # Send webhook notification
        # Log payment for accounting
        pass

    @event_handler(InvoiceCreatedEvent)
    async def on_invoice_created(self, event: InvoiceCreatedEvent) -> None:
        # Log invoice creation
        # Send webhook notification
        # Update metrics
        pass
```

### Global Event Bus Integration

Lightning events integrate with OpenFatture's global event system:

```python
# In lifespan.py
async def initialize_lightning_events():
    if settings.lightning_enabled:
        handlers = LightningEventHandlers(repository)
        global_event_bus.register_handler(
            PaymentReceivedEvent,
            handlers.on_payment_received
        )
        global_event_bus.register_handler(
            InvoiceCreatedEvent,
            handlers.on_invoice_created
        )
```

---

## Webhook Implementation

### Webhook Handler

FastAPI-based webhook endpoint for external integrations:

```python
class LightningWebhookHandler:
    def __init__(
        self,
        webhook_secret: str,
        event_bus: EventBus,
        repository: LightningRepository
    ):
        self.webhook_secret = webhook_secret
        self.event_bus = event_bus
        self.repository = repository

    async def handle_webhook(
        self,
        payload: dict,
        signature: str | None = None
    ) -> dict:
        # Verify webhook signature
        if signature and not self._verify_signature(payload, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Process webhook event
        event_type = payload.get('event')

        if event_type == 'payment_received':
            await self._handle_payment_received(payload)
        elif event_type == 'invoice_created':
            await self._handle_invoice_created(payload)
        # ... other event types

        return {'status': 'ok'}

    def _verify_signature(self, payload: dict, signature: str) -> bool:
        """Verify webhook signature using HMAC-SHA256"""
        message = json.dumps(payload, sort_keys=True)
        expected = hmac.new(
            self.webhook_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)
```

### Webhook Payloads

#### Payment Received

```json
{
  "event": "payment_received",
  "invoice_id": "lnbc123...",
  "payment_hash": "abc123...",
  "amount_sats": 11111,
  "amount_eur": 500.00,
  "fee_sats": 0,
  "fee_eur": 0.00,
  "timestamp": "2025-01-15T10:30:00Z",
  "description": "Invoice payment",
  "metadata": {
    "original_invoice": "INV-001",
    "client_id": "123"
  }
}
```

#### Invoice Created

```json
{
  "event": "invoice_created",
  "invoice_id": "lnbc456...",
  "payment_hash": "def456...",
  "amount_sats": 22222,
  "amount_eur": 1000.00,
  "expiry_time": "2025-01-16T10:30:00Z",
  "description": "Service payment",
  "payment_request": "lnbc222220n1...",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

### Security Considerations

1. **Signature Verification**: All webhooks include HMAC-SHA256 signatures
2. **HTTPS Only**: Webhooks require HTTPS endpoints
3. **Secret Rotation**: Support for webhook secret rotation
4. **Rate Limiting**: Built-in rate limiting to prevent abuse
5. **Idempotency**: Webhook processing is idempotent

---

## Rate Provider System

### Multi-Provider Architecture

```python
class RateProvider:
    def __init__(self, providers: list[ExchangeProvider]):
        self.providers = providers
        self.cache = TTLCache(maxsize=1, ttl=300)  # 5 min cache

    async def get_rate(self) -> Decimal:
        """Get BTC/EUR rate with fallback logic"""
        # Try primary provider (CoinGecko)
        try:
            return await self._get_coingecko_rate()
        except Exception:
            pass

        # Try secondary provider (CoinMarketCap)
        try:
            return await self._get_cmc_rate()
        except Exception:
            pass

        # Use fallback rate
        return self.fallback_rate
```

### CoinGecko Integration

```python
class CoinGeckoProvider:
    async def get_btc_eur_rate(self) -> Decimal:
        async with aiohttp.ClientSession() as session:
            headers = {}
            if self.api_key:
                headers['x-cg-demo-api-key'] = self.api_key

            async with session.get(
                'https://api.coingecko.com/api/v3/simple/price',
                params={'ids': 'bitcoin', 'vs_currencies': 'eur'},
                headers=headers
            ) as response:
                data = await response.json()
                return Decimal(str(data['bitcoin']['eur']))
```

### CoinMarketCap Integration

```python
class CMCProvider:
    async def get_btc_eur_rate(self) -> Decimal:
        headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accept': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest',
                params={'symbol': 'BTC', 'convert': 'EUR'},
                headers=headers
            ) as response:
                data = await response.json()
                return Decimal(str(data['data']['BTC']['quote']['EUR']['price']))
```

---

## Data Persistence

### Repository Pattern

```python
class LightningRepository:
    def __init__(self, session_factory: Callable):
        self.session_factory = session_factory

    async def save_invoice(self, invoice: LightningInvoice) -> None:
        async with self.session_factory() as session:
            # Convert domain object to database model
            db_invoice = LightningInvoiceModel.from_domain(invoice)
            session.add(db_invoice)
            await session.commit()

    async def get_invoice_by_hash(self, payment_hash: str) -> LightningInvoice | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(LightningInvoiceModel)
                .where(LightningInvoiceModel.payment_hash == payment_hash)
            )
            db_invoice = result.scalar_one_or_none()
            return db_invoice.to_domain() if db_invoice else None
```

### Database Models

```python
class LightningInvoiceModel(Base):
    __tablename__ = 'lightning_invoices'

    id: Mapped[str] = mapped_column(primary_key=True)
    amount_sats: Mapped[int] = mapped_column(Integer)
    amount_eur: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2))
    description: Mapped[str] = mapped_column(String)
    payment_request: Mapped[str] = mapped_column(String, unique=True)
    payment_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    expiry_time: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
```

---

## CLI Integration

### Command Structure

```python
# lightning_cli.py
@app.command()
async def status() -> None:
    """Show Lightning network status"""
    async with get_lnd_client() as client:
        info = await client.get_info()
        channels = await client.list_channels()

        console.print(f"✅ LND Connected: {info.alias}")
        console.print(f"📊 Channels: {len(channels)} total")
        console.print(f"💰 Capacity: {sum(c.capacity for c in channels)} sats")

@app.command()
async def invoice_create(
    amount: float,
    description: str,
    expiry_hours: int = 24
) -> None:
    """Create a new Lightning invoice"""
    service = InvoiceService(
        lnd_client=get_lnd_client(),
        rate_provider=get_rate_provider(),
        repository=get_repository(),
        event_bus=get_event_bus()
    )

    invoice = await service.create_invoice(
        amount_eur=Decimal(str(amount)),
        description=description,
        expiry_hours=expiry_hours
    )

    console.print(f"⚡ Invoice created: {invoice.id}")
    console.print(f"💰 Amount: {invoice.amount_eur} EUR ({invoice.amount_sats} sats)")
    console.print(f"⏰ Expires: {invoice.expiry_time}")
    console.print(f"📄 Payment Request: {invoice.payment_request}")
```

### Lifespan Management

```python
# lifespan.py
async def initialize_lightning():
    if settings.lightning_enabled:
        # Initialize LND client
        lnd_client = LNDClient.from_settings(settings)

        # Test connection
        try:
            await lnd_client.get_info()
            logger.info("Lightning: LND connection established")
        except Exception as e:
            logger.warning(f"Lightning: LND connection failed: {e}")
            return

        # Start background services
        if settings.lightning_liquidity_enabled:
            liquidity_service = LiquidityService(lnd_client)
            # Start liquidity monitoring task

        # Register event handlers
        lightning_handlers = LightningEventHandlers()
        global_event_bus.register_handlers(lightning_handlers)

        # Start payment monitoring
        payment_monitor = PaymentMonitor(lnd_client, global_event_bus)
        # Start monitoring task
```

---

## Testing Strategy

### Unit Tests

```python
# Test invoice creation
@pytest.mark.asyncio
async def test_create_invoice():
    # Mock dependencies
    lnd_client = Mock()
    rate_provider = Mock()
    repository = Mock()
    event_bus = Mock()

    # Setup mocks
    rate_provider.get_rate.return_value = Decimal('45000')
    lnd_client.add_invoice.return_value = Mock(
        payment_request='lnbc123...',
        payment_hash='hash123'
    )

    # Test service
    service = InvoiceService(lnd_client, rate_provider, repository, event_bus)
    invoice = await service.create_invoice(
        amount_eur=Decimal('100'),
        description='Test payment'
    )

    assert invoice.amount_eur == Decimal('100')
    assert invoice.amount_sats == 2222  # 100 / 45000 * 100M
```

### Integration Tests

```python
# Test with real LND (requires LND running)
@pytest.mark.integration
@pytest.mark.asyncio
async def test_lnd_integration():
    client = LNDClient(
        host='localhost:10009',
        cert_path=Path('~/.lnd/tls.cert'),
        macaroon_path=Path('~/.lnd/admin.macaroon')
    )

    # Test basic connectivity
    info = await client.get_info()
    assert info.identity_pubkey

    # Test invoice creation
    invoice = await client.add_invoice(
        value_sats=1000,
        memo='Integration test'
    )
    assert invoice.payment_request.startswith('lnbc')
```

### E2E Tests

```python
# Full workflow test
@pytest.mark.e2e
async def test_payment_workflow():
    # Create invoice
    invoice = await invoice_service.create_invoice(
        amount_eur=Decimal('10'),
        description='E2E test'
    )

    # Simulate payment (would need real wallet)
    # payment_hash = await wallet.pay_invoice(invoice.payment_request)

    # Verify settlement
    # updated_invoice = await invoice_service.get_invoice(invoice.id)
    # assert updated_invoice.status == InvoiceStatus.SETTLED
```

---

## Performance Considerations

### Connection Pooling

- gRPC connections are pooled and reused
- Connection timeouts prevent hanging requests
- Circuit breaker prevents cascade failures

### Caching Strategy

- BTC/EUR rates cached for 5 minutes
- Invoice data cached in application layer
- Channel information refreshed periodically

### Async Processing

- All LND operations are async
- Event handling runs in background tasks
- Webhook processing is non-blocking

### Resource Management

- Automatic cleanup of expired connections
- Memory-efficient data structures
- Configurable timeouts and limits

---

## Monitoring & Observability

### Metrics

```python
class LightningMetrics:
    invoices_created: Counter
    payments_received: Counter
    payments_failed: Counter
    lnd_connection_errors: Counter
    rate_provider_errors: Counter
    webhook_delivery_attempts: Counter
    webhook_delivery_success: Counter
```

### Logging

Structured logging for all Lightning operations:

```python
logger.info(
    "Lightning invoice created",
    extra={
        "invoice_id": invoice.id,
        "amount_eur": invoice.amount_eur,
        "amount_sats": invoice.amount_sats,
        "description": invoice.description
    }
)
```

### Health Checks

```python
async def lightning_health_check() -> HealthStatus:
    """Comprehensive health check for Lightning integration"""
    checks = []

    # LND connectivity
    try:
        await lnd_client.get_info()
        checks.append(HealthCheck("lnd_connection", True))
    except Exception as e:
        checks.append(HealthCheck("lnd_connection", False, str(e)))

    # Channel liquidity
    channels = await lnd_client.list_channels()
    total_capacity = sum(c.capacity for c in channels)
    checks.append(HealthCheck(
        "channel_capacity",
        total_capacity > 0,
        f"Total capacity: {total_capacity} sats"
    ))

    return HealthStatus("lightning", all(c.healthy for c in checks), checks)
```

---

## Security Considerations

### Authentication

- Macaroon-based authentication with LND
- TLS certificate validation
- Webhook signature verification

### Authorization

- Fine-grained permissions via macaroons
- Read-only operations where possible
- Audit logging for all operations

### Data Protection

- Sensitive data encrypted at rest
- No logging of payment secrets
- Secure webhook secret handling

### Network Security

- Firewall rules for LND ports
- VPN recommended for remote access
- Regular security updates

---

## Deployment Considerations

### Docker Integration

```dockerfile
# LND container
FROM lightninglabs/lnd:v0.17.0-beta

# OpenFatture container with Lightning support
FROM python:3.12
COPY . /app
RUN pip install -r requirements.txt
ENV LIGHTNING_ENABLED=true
ENV LIGHTNING_HOST=lnd:10009
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: openfatture
spec:
  template:
    spec:
      containers:
      - name: openfatture
        env:
        - name: LIGHTNING_ENABLED
          value: "true"
        - name: LIGHTNING_HOST
          value: "lnd-service:10009"
      - name: lnd
        image: lightninglabs/lnd:v0.17.0-beta
        ports:
        - containerPort: 10009
```

### High Availability

- Multiple LND nodes with load balancing
- Database replication for invoice data
- Webhook retry mechanisms
- Monitoring and alerting

---

## Future Enhancements

### Planned Features

1. **Multi-Node Support**: Connect to multiple LND nodes
2. **Channel Management**: Automated channel opening/closing
3. **Routing Optimization**: Smart payment routing
4. **HODL Invoices**: Hold payments until conditions met
5. **AMP Payments**: Atomic multi-path payments

### API Extensions

- REST API for invoice management
- GraphQL API for advanced queries
- WebSocket real-time updates
- Mobile wallet integration

### Advanced Liquidity

- **Circular Rebalancing**: Automated circular payments
- **External Liquidity**: Integration with liquidity providers
- **Liquidity Ads**: Channel advertisement for inbound liquidity
- **Splicing**: Dynamic channel capacity changes

---

*Last updated: January 2025*
