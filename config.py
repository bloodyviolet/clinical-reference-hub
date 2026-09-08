"""Runtime configuration for the Medical API.

Configuration is intentionally environment-variable based. Production deployments should
use an OS/container secret/environment mechanism rather than committing a .env file.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import os
import ipaddress
from pathlib import Path
from urllib.parse import urlsplit
from typing import Mapping

BASE_DIR = Path(__file__).resolve().parent

_TRUE = {"1", "true", "yes", "on"}
_FALSE = {"0", "false", "no", "off"}


def _bool(value: str | None, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    normalised = value.strip().lower()
    if normalised in _TRUE:
        return True
    if normalised in _FALSE:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def _int(value: str | None, default: int, *, minimum: int = 0, maximum: int | None = None) -> int:
    if value is None or not value.strip():
        result = default
    else:
        try:
            result = int(value)
        except ValueError as exc:
            raise ValueError(f"Invalid integer value: {value!r}") from exc
    if result < minimum or (maximum is not None and result > maximum):
        upper = f" and <= {maximum}" if maximum is not None else ""
        raise ValueError(f"Integer value must be >= {minimum}{upper}: {result}")
    return result


def _csv(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None or not value.strip():
        return default
    items = tuple(part.strip() for part in value.split(",") if part.strip())
    return items or default


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    enable_api_docs: bool = True
    enable_hsts: bool = False
    enable_sae: bool = True
    enforce_dependency_lock: bool = False
    allowed_hosts: tuple[str, ...] = ("*",)
    public_origin: str | None = None

    rate_limit_enabled: bool = False
    api_rate_limit_per_minute: int = 120
    search_rate_limit_per_minute: int = 60
    rate_limit_max_clients: int = 10_000

    log_level: str = "INFO"
    json_logs: bool = False
    log_client_ip: bool = False

    bind_host: str = "127.0.0.1"
    bind_port: int = 8000
    workers: int = 1
    trusted_proxies: tuple[str, ...] = ("127.0.0.1", "::1")
    graceful_shutdown_seconds: int = 30
    limit_concurrency: int = 200
    backlog: int = 1024
    keep_alive_seconds: int = 5

    sqlite_busy_timeout_ms: int = 5_000
    backup_directory: Path = field(default_factory=lambda: BASE_DIR / "backups")

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def forwarded_allow_ips(self) -> str:
        return ",".join(self.trusted_proxies)

    def validate(self) -> tuple[list[str], list[str]]:
        errors: list[str] = []
        warnings: list[str] = []
        if self.environment not in {"development", "test", "production"}:
            errors.append("MEDICAL_API_ENV must be development, test, or production.")
        if not self.allowed_hosts:
            errors.append("At least one MEDICAL_API_ALLOWED_HOSTS entry is required.")
        for host in self.allowed_hosts:
            if "://" in host or "/" in host or " " in host:
                errors.append(f"Invalid MEDICAL_API_ALLOWED_HOSTS entry: {host!r} (hostnames only; no scheme/path).")
        for proxy in self.trusted_proxies:
            try:
                ipaddress.ip_network(proxy, strict=False)
            except ValueError:
                errors.append(f"Invalid MEDICAL_API_TRUSTED_PROXIES IP/CIDR: {proxy!r}.")
        if self.workers < 1:
            errors.append("MEDICAL_API_WORKERS must be at least 1.")
        if self.search_rate_limit_per_minute > self.api_rate_limit_per_minute:
            warnings.append("Search rate limit exceeds the general API rate limit; the lower effective limit wins.")
        if self.is_production:
            if "*" in self.allowed_hosts:
                errors.append("Wildcard MEDICAL_API_ALLOWED_HOSTS is forbidden in production.")
            if any(proxy == "*" for proxy in self.trusted_proxies):
                errors.append("Wildcard MEDICAL_API_TRUSTED_PROXIES is forbidden in production.")
            if not self.public_origin:
                errors.append("MEDICAL_API_PUBLIC_ORIGIN is required in production.")
            else:
                origin = urlsplit(self.public_origin)
                if origin.scheme != "https" or not origin.hostname:
                    errors.append("MEDICAL_API_PUBLIC_ORIGIN must be an absolute https:// origin in production.")
                if origin.username or origin.password or origin.query or origin.fragment or origin.path not in {"", "/"}:
                    errors.append("MEDICAL_API_PUBLIC_ORIGIN must contain only scheme + host (+ optional port), no credentials/path/query/fragment.")
                if origin.hostname:
                    host_allowed = any(
                        allowed == origin.hostname
                        or (allowed.startswith("*.") and origin.hostname.endswith(allowed[1:]))
                        for allowed in self.allowed_hosts
                    )
                    if not host_allowed:
                        errors.append("MEDICAL_API_PUBLIC_ORIGIN hostname must be included in MEDICAL_API_ALLOWED_HOSTS.")
            if not self.enable_hsts:
                errors.append("MEDICAL_API_HSTS must be enabled in production.")
            if not self.rate_limit_enabled:
                errors.append("MEDICAL_API_RATE_LIMIT_ENABLED must be enabled in production.")
            if self.enable_api_docs:
                warnings.append("API docs are enabled in production; disable them unless intentionally public.")
            if self.workers > 1:
                warnings.append(
                    "The application rate limiter is per worker. With multiple workers, enforce the authoritative "
                    "rate limit at the reverse proxy as supplied in deploy/nginx/medical-api.conf."
                )
        return errors, warnings

    def assert_valid(self) -> list[str]:
        errors, warnings = self.validate()
        if errors:
            raise RuntimeError("Unsafe/invalid Medical API configuration: " + " ".join(errors))
        return warnings

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        env = os.environ if environ is None else environ
        environment = env.get("MEDICAL_API_ENV", "development").strip().lower() or "development"
        production = environment == "production"
        default_docs = not production
        default_hsts = production
        default_rate_limit = production
        default_json_logs = production

        backup_raw = env.get("MEDICAL_API_BACKUP_DIR", "").strip()
        backup_dir = Path(backup_raw).expanduser() if backup_raw else BASE_DIR / "backups"

        return cls(
            environment=environment,
            enable_api_docs=_bool(env.get("MEDICAL_API_ENABLE_DOCS"), default_docs),
            enable_hsts=_bool(env.get("MEDICAL_API_HSTS"), default_hsts),
            enable_sae=_bool(env.get("MEDICAL_API_ENABLE_SAE"), True),
            enforce_dependency_lock=_bool(env.get("MEDICAL_API_ENFORCE_DEPENDENCY_LOCK"), production),
            allowed_hosts=_csv(env.get("MEDICAL_API_ALLOWED_HOSTS"), ("*",) if not production else ()),
            public_origin=(env.get("MEDICAL_API_PUBLIC_ORIGIN") or "").strip().rstrip("/") or None,
            rate_limit_enabled=_bool(env.get("MEDICAL_API_RATE_LIMIT_ENABLED"), default_rate_limit),
            api_rate_limit_per_minute=_int(env.get("MEDICAL_API_RATE_LIMIT_PER_MINUTE"), 120, minimum=1, maximum=100_000),
            search_rate_limit_per_minute=_int(env.get("MEDICAL_API_SEARCH_RATE_LIMIT_PER_MINUTE"), 60, minimum=1, maximum=100_000),
            rate_limit_max_clients=_int(env.get("MEDICAL_API_RATE_LIMIT_MAX_CLIENTS"), 10_000, minimum=100, maximum=1_000_000),
            log_level=(env.get("MEDICAL_API_LOG_LEVEL", "INFO").strip().upper() or "INFO"),
            json_logs=_bool(env.get("MEDICAL_API_JSON_LOGS"), default_json_logs),
            log_client_ip=_bool(env.get("MEDICAL_API_LOG_CLIENT_IP"), False),
            bind_host=(env.get("MEDICAL_API_BIND_HOST", "127.0.0.1").strip() or "127.0.0.1"),
            bind_port=_int(env.get("MEDICAL_API_PORT"), 8000, minimum=1, maximum=65535),
            workers=_int(env.get("MEDICAL_API_WORKERS"), 1, minimum=1, maximum=32),
            trusted_proxies=_csv(env.get("MEDICAL_API_TRUSTED_PROXIES"), ("127.0.0.1", "::1")),
            graceful_shutdown_seconds=_int(env.get("MEDICAL_API_GRACEFUL_SHUTDOWN_SECONDS"), 30, minimum=1, maximum=300),
            limit_concurrency=_int(env.get("MEDICAL_API_LIMIT_CONCURRENCY"), 200, minimum=1, maximum=100_000),
            backlog=_int(env.get("MEDICAL_API_BACKLOG"), 1024, minimum=16, maximum=65_535),
            keep_alive_seconds=_int(env.get("MEDICAL_API_KEEP_ALIVE_SECONDS"), 5, minimum=1, maximum=120),
            sqlite_busy_timeout_ms=_int(env.get("MEDICAL_API_SQLITE_BUSY_TIMEOUT_MS"), 5_000, minimum=100, maximum=120_000),
            backup_directory=backup_dir,
        )


def load_settings() -> Settings:
    return Settings.from_env()
