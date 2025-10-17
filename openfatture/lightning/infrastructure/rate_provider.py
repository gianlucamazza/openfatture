"""Exchange rate providers for BTC conversion.

Provides reliable BTC/EUR exchange rates with caching and fallback mechanisms.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

import httpx

from ...utils.config import Settings


@dataclass
class ExchangeRate:
    """Exchange rate data point."""

    btc_eur_rate: Decimal
    source: str
    timestamp: int
    ttl_seconds: int

    @property
    def is_expired(self) -> bool:
        """Check if rate has expired."""
        return time.time() > (self.timestamp + self.ttl_seconds)


class ExchangeProvider(ABC):
    """Abstract base class for exchange rate providers."""

    def __init__(self, name: str, api_key: str | None = None):
        self.name = name
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=5.0), headers={"User-Agent": "OpenFatture/1.0"}
        )

    @abstractmethod
    async def get_btc_eur_rate(self) -> Decimal:
        """Get current BTC/EUR exchange rate."""
        pass

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class CoinGeckoProvider(ExchangeProvider):
    """CoinGecko exchange rate provider (free tier)."""

    def __init__(self, api_key: str | None = None):
        super().__init__("coingecko", api_key)
        self.base_url = "https://api.coingecko.com/api/v3"

    async def get_btc_eur_rate(self) -> Decimal:
        """Get BTC/EUR rate from CoinGecko."""
        url = f"{self.base_url}/simple/price"
        params = {"ids": "bitcoin", "vs_currencies": "eur", "precision": "8"}

        if self.api_key:
            params["x_cg_demo_api_key"] = self.api_key

        response = await self.client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        rate = Decimal(str(data["bitcoin"]["eur"]))

        return rate


class CoinMarketCapProvider(ExchangeProvider):
    """CoinMarketCap exchange rate provider (requires API key)."""

    def __init__(self, api_key: str):
        super().__init__("coinmarketcap", api_key)
        self.base_url = "https://pro-api.coinmarketcap.com/v1"

    async def get_btc_eur_rate(self) -> Decimal:
        """Get BTC/EUR rate from CoinMarketCap."""
        if not self.api_key:
            raise ValueError("CoinMarketCap requires API key")

        url = f"{self.base_url}/cryptocurrency/quotes/latest"
        headers = {"X-CMC_PRO_API_KEY": self.api_key, "Accept": "application/json"}
        params = {"symbol": "BTC", "convert": "EUR"}

        response = await self.client.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        rate = Decimal(str(data["data"]["BTC"]["quote"]["EUR"]["price"]))

        return rate


class FallbackProvider(ExchangeProvider):
    """Fallback provider with static rates for emergencies."""

    def __init__(self, fallback_rate: Decimal = Decimal("45000.00")):
        super().__init__("fallback")
        self.fallback_rate = fallback_rate

    async def get_btc_eur_rate(self) -> Decimal:
        """Return fallback rate."""
        return self.fallback_rate


class RateCache:
    """Simple in-memory cache for exchange rates."""

    def __init__(self):
        self._cache: dict[str, ExchangeRate] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> ExchangeRate | None:
        """Get cached rate if not expired."""
        async with self._lock:
            rate = self._cache.get(key)
            if rate and not rate.is_expired:
                return rate
            elif rate and rate.is_expired:
                # Remove expired entry
                del self._cache[key]
            return None

    async def set(self, key: str, rate: ExchangeRate):
        """Cache exchange rate."""
        async with self._lock:
            self._cache[key] = rate

    async def clear(self):
        """Clear all cached rates."""
        async with self._lock:
            self._cache.clear()


class BTCConversionService:
    """Production BTC conversion service with multiple providers and caching."""

    def __init__(
        self,
        providers: list[ExchangeProvider],
        cache: RateCache | None = None,
        cache_ttl_seconds: int = 300,  # 5 minutes
        circuit_breaker_failures: int = 3,
        circuit_breaker_timeout: int = 60,
    ):
        self.providers = providers
        self.cache = cache or RateCache()
        self.cache_ttl = cache_ttl_seconds

        # Circuit breaker state
        self.circuit_failures = 0
        self.circuit_last_failure: float = 0.0
        self.circuit_max_failures = circuit_breaker_failures
        self.circuit_timeout = circuit_breaker_timeout

        # Rate limiting
        self._last_request_time: float = 0.0
        self._min_request_interval = 1.0  # 1 second between requests

    async def convert_eur_to_btc(self, eur_amount: Decimal) -> Decimal:
        """Convert EUR amount to BTC.

        Args:
            eur_amount: Amount in EUR

        Returns:
            Amount in BTC (satoshi precision)

        Raises:
            ValueError: If amount is invalid
            RuntimeError: If all providers fail
        """
        if eur_amount <= 0:
            raise ValueError("Amount must be positive")

        # Get current BTC/EUR rate
        btc_eur_rate = await self._get_btc_eur_rate()

        # Convert EUR to BTC
        btc_amount = eur_amount / btc_eur_rate

        # Return with 8 decimal precision (satoshi level)
        return btc_amount.quantize(Decimal("0.00000001"))

    async def convert_btc_to_eur(self, btc_amount: Decimal) -> Decimal:
        """Convert BTC amount to EUR.

        Args:
            btc_amount: Amount in BTC

        Returns:
            Amount in EUR (cent precision)

        Raises:
            ValueError: If amount is invalid
            RuntimeError: If all providers fail
        """
        if btc_amount <= 0:
            raise ValueError("Amount must be positive")

        # Get current BTC/EUR rate
        btc_eur_rate = await self._get_btc_eur_rate()

        # Convert BTC to EUR
        eur_amount = btc_amount * btc_eur_rate

        # Return with 2 decimal precision (cent level)
        return eur_amount.quantize(Decimal("0.01"))

    async def _get_btc_eur_rate(self) -> Decimal:
        """Get current BTC/EUR exchange rate with caching and fallback."""
        cache_key = "btc_eur_rate"

        # Check cache first
        cached_rate = await self.cache.get(cache_key)
        if cached_rate:
            return cached_rate.btc_eur_rate

        # Check circuit breaker
        if self._is_circuit_open():
            # Use fallback provider
            fallback_provider = next(
                (p for p in self.providers if isinstance(p, FallbackProvider)), FallbackProvider()
            )
            rate = await fallback_provider.get_btc_eur_rate()
            return rate

        # Try providers in order
        for provider in self.providers:
            if isinstance(provider, FallbackProvider):
                continue  # Skip fallback unless all others fail

            try:
                # Rate limiting
                await self._rate_limit()

                rate = await provider.get_btc_eur_rate()

                # Validate rate is reasonable (between 10k and 200k EUR)
                if not (Decimal("10000") <= rate <= Decimal("200000")):
                    raise ValueError(f"Unreasonable rate from {provider.name}: {rate}")

                # Cache successful result
                exchange_rate = ExchangeRate(
                    btc_eur_rate=rate,
                    source=provider.name,
                    timestamp=int(time.time()),
                    ttl_seconds=self.cache_ttl,
                )
                await self.cache.set(cache_key, exchange_rate)

                # Reset circuit breaker
                self.circuit_failures = 0

                return rate

            except Exception as e:
                print(f"Provider {provider.name} failed: {e}")
                self.circuit_failures += 1
                self.circuit_last_failure = time.time()
                continue

        # All providers failed, use fallback
        fallback_provider = next(
            (p for p in self.providers if isinstance(p, FallbackProvider)), FallbackProvider()
        )
        rate = await fallback_provider.get_btc_eur_rate()
        print(f"Using fallback rate: {rate}")
        return rate

    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open."""
        if self.circuit_failures < self.circuit_max_failures:
            return False

        # Check if timeout has passed
        if time.time() - self.circuit_last_failure >= self.circuit_timeout:
            # Half-open state - allow one attempt
            self.circuit_failures = self.circuit_max_failures - 1
            return False

        return True

    async def _rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)

        self._last_request_time = time.time()

    async def get_rate_info(self) -> dict:
        """Get information about current rate and providers."""
        cache_key = "btc_eur_rate"
        cached_rate = await self.cache.get(cache_key)

        return {
            "current_rate": float(cached_rate.btc_eur_rate) if cached_rate else None,
            "rate_source": cached_rate.source if cached_rate else None,
            "rate_timestamp": cached_rate.timestamp if cached_rate else None,
            "circuit_breaker_open": self._is_circuit_open(),
            "circuit_failures": self.circuit_failures,
            "providers": [p.name for p in self.providers],
            "cache_ttl": self.cache_ttl,
        }

    async def close(self):
        """Close all provider connections."""
        for provider in self.providers:
            await provider.close()


def create_btc_conversion_service(settings: Settings) -> BTCConversionService:
    """Factory function to create BTC conversion service from settings."""
    providers: list[ExchangeProvider] = []

    # CoinGecko (free)
    if getattr(settings, "lightning_coingecko_enabled", True):
        providers.append(
            CoinGeckoProvider(api_key=getattr(settings, "lightning_coingecko_api_key", None))
        )

    # CoinMarketCap (paid)
    if getattr(settings, "lightning_cmc_enabled", False):
        api_key = getattr(settings, "lightning_cmc_api_key", None)
        if api_key:
            providers.append(CoinMarketCapProvider(api_key))

    # Fallback (always included)
    providers.append(
        FallbackProvider(
            fallback_rate=Decimal(str(getattr(settings, "lightning_fallback_rate", "45000.00")))
        )
    )

    cache_ttl = getattr(settings, "lightning_rate_cache_ttl", 300)

    return BTCConversionService(providers=providers, cache_ttl_seconds=cache_ttl)
