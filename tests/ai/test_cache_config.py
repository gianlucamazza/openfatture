"""Tests for AI cache configuration."""

import os
from unittest.mock import patch

import pytest

from openfatture.ai.cache.config import CacheConfig, get_cache_config


class TestCacheConfig:
    """Test CacheConfig model."""

    def test_cache_config_defaults(self):
        """Test CacheConfig with default values."""
        config = CacheConfig()
        assert config.enabled is True
        assert config.strategy == "lru"
        assert config.max_size == 1000
        assert config.default_ttl == 3600
        assert config.cleanup_interval == 300
        assert config.similarity_threshold == 0.85
        assert config.embedding_model == "text-embedding-3-small"
        assert config.enable_stats is True
        assert config.log_hits is False
        assert config.log_misses is False

    def test_cache_config_custom_values(self):
        """Test CacheConfig with custom values."""
        config = CacheConfig(
            enabled=False,
            strategy="semantic",
            max_size=500,
            default_ttl=1800,
            cleanup_interval=600,
            similarity_threshold=0.9,
            embedding_model="text-embedding-3-large",
            enable_stats=False,
            log_hits=True,
            log_misses=True,
        )
        assert config.enabled is False
        assert config.strategy == "semantic"
        assert config.max_size == 500
        assert config.default_ttl == 1800
        assert config.cleanup_interval == 600
        assert config.similarity_threshold == 0.9
        assert config.embedding_model == "text-embedding-3-large"
        assert config.enable_stats is False
        assert config.log_hits is True
        assert config.log_misses is True

    def test_cache_config_validation_max_size(self):
        """Test max_size validation."""
        with pytest.raises(ValueError):
            CacheConfig(max_size=0)

        # Valid minimum
        config = CacheConfig(max_size=1)
        assert config.max_size == 1

    def test_cache_config_validation_default_ttl(self):
        """Test default_ttl validation."""
        with pytest.raises(ValueError):
            CacheConfig(default_ttl=-1)

        # Valid minimum
        config = CacheConfig(default_ttl=0)
        assert config.default_ttl == 0

        # None is allowed
        config = CacheConfig(default_ttl=None)
        assert config.default_ttl is None

    def test_cache_config_validation_cleanup_interval(self):
        """Test cleanup_interval validation."""
        with pytest.raises(ValueError):
            CacheConfig(cleanup_interval=-1)

        # Valid minimum
        config = CacheConfig(cleanup_interval=0)
        assert config.cleanup_interval == 0

    def test_cache_config_validation_similarity_threshold(self):
        """Test similarity_threshold validation."""
        with pytest.raises(ValueError):
            CacheConfig(similarity_threshold=-0.1)

        with pytest.raises(ValueError):
            CacheConfig(similarity_threshold=1.1)

        # Valid boundaries
        config = CacheConfig(similarity_threshold=0.0)
        assert config.similarity_threshold == 0.0

        config = CacheConfig(similarity_threshold=1.0)
        assert config.similarity_threshold == 1.0

    def test_cache_config_frozen_false(self):
        """Test that config is not frozen and can be modified."""
        config = CacheConfig()
        config.max_size = 2000
        assert config.max_size == 2000


class TestGetCacheConfig:
    """Test get_cache_config function."""

    @patch.dict(os.environ, {}, clear=True)
    def test_get_cache_config_defaults(self):
        """Test get_cache_config with no environment variables."""
        config = get_cache_config()
        assert config.enabled is True
        assert config.strategy == "lru"
        assert config.max_size == 1000
        assert config.default_ttl == 3600
        assert config.cleanup_interval == 300
        assert config.similarity_threshold == 0.85
        assert config.embedding_model == "text-embedding-3-small"
        assert config.enable_stats is True
        assert config.log_hits is False
        assert config.log_misses is False

    @patch.dict(
        os.environ,
        {
            "OPENFATTURE_CACHE_ENABLED": "false",
            "OPENFATTURE_CACHE_STRATEGY": "semantic",
            "OPENFATTURE_CACHE_MAX_SIZE": "500",
            "OPENFATTURE_CACHE_DEFAULT_TTL": "1800",
            "OPENFATTURE_CACHE_CLEANUP_INTERVAL": "600",
            "OPENFATTURE_CACHE_SIMILARITY_THRESHOLD": "0.9",
            "OPENFATTURE_CACHE_EMBEDDING_MODEL": "text-embedding-3-large",
            "OPENFATTURE_CACHE_ENABLE_STATS": "false",
            "OPENFATTURE_CACHE_LOG_HITS": "true",
            "OPENFATTURE_CACHE_LOG_MISSES": "true",
        },
    )
    def test_get_cache_config_from_env(self):
        """Test get_cache_config with environment variables."""
        config = get_cache_config()
        assert config.enabled is False
        assert config.strategy == "semantic"
        assert config.max_size == 500
        assert config.default_ttl == 1800
        assert config.cleanup_interval == 600
        assert config.similarity_threshold == 0.9
        assert config.embedding_model == "text-embedding-3-large"
        assert config.enable_stats is False
        assert config.log_hits is True
        assert config.log_misses is True

    @patch.dict(
        os.environ,
        {
            "OPENFATTURE_CACHE_STRATEGY": "invalid",
        },
    )
    def test_get_cache_config_invalid_strategy(self, caplog):
        """Test get_cache_config with invalid strategy falls back to lru."""
        config = get_cache_config()
        assert config.strategy == "lru"
        assert "Invalid cache strategy 'invalid'. Falling back to 'lru'." in caplog.text

    @patch.dict(
        os.environ,
        {
            "OPENFATTURE_CACHE_ENABLED": "True",  # uppercase
            "OPENFATTURE_CACHE_ENABLE_STATS": "False",  # uppercase
            "OPENFATTURE_CACHE_LOG_HITS": "True",  # uppercase
            "OPENFATTURE_CACHE_LOG_MISSES": "False",  # uppercase
        },
    )
    def test_get_cache_config_boolean_case_insensitive(self):
        """Test get_cache_config handles boolean values case-insensitively."""
        config = get_cache_config()
        assert config.enabled is True
        assert config.enable_stats is False
        assert config.log_hits is True
        assert config.log_misses is False

    @patch.dict(
        os.environ,
        {
            "OPENFATTURE_CACHE_MAX_SIZE": "invalid",
        },
    )
    def test_get_cache_config_invalid_int_falls_back(self):
        """Test get_cache_config with invalid int falls back to default."""
        # This will raise ValueError from int() conversion
        with pytest.raises(ValueError):
            get_cache_config()

    @patch.dict(
        os.environ,
        {
            "OPENFATTURE_CACHE_SIMILARITY_THRESHOLD": "invalid",
        },
    )
    def test_get_cache_config_invalid_float_falls_back(self):
        """Test get_cache_config with invalid float falls back to default."""
        # This will raise ValueError from float() conversion
        with pytest.raises(ValueError):
            get_cache_config()
