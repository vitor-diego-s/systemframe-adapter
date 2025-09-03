# ...existing code...
import os
import yaml
import time
import threading
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("incident-mirror")
logging.basicConfig(level=logging.INFO)

CONFIG_MAP_PATH = os.getenv("CONFIG_MAP_PATH", "config.yaml")

with open(CONFIG_MAP_PATH, "r") as f:
    cfg = yaml.safe_load(f) or {}

# Simple configuration holder for a host entry
class Config:
    def __init__(
        self,
        id: str,
        name: str,
        role: str,
        platform: str,
        endpoint: str,
        port: int = 443,
        protocol: str = "https",
        credentials: Optional[Dict[str, str]] = None,
        polling: Optional[Dict[str, Any]] = None,
        webhook: Optional[Dict[str, Any]] = None,
        raw: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.name = name
        self.role = role
        self.platform = platform
        self.endpoint = endpoint
        self.port = port
        self.protocol = protocol
        self.credentials = credentials or {}
        self.polling = polling or {"enabled": False}
        self.webhook = webhook or {"enabled": False}
        self.raw = raw or {}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]):
        # Resolve credentials from environment variables if credentials_env provided
        creds = {}
        creds_env = d.get("credentials_env", {})
        for key, envvar in creds_env.items():
            creds[key] = os.getenv(envvar)

        return cls(
            id=d.get("id"),
            name=d.get("name"),
            role=d.get("role"),
            platform=d.get("platform"),
            endpoint=d.get("endpoint"),
            port=d.get("port", 443),
            protocol=d.get("protocol", "https"),
            credentials=creds,
            polling=d.get("polling", {"enabled": False}),
            webhook=d.get("webhook", {"enabled": False}),
            raw=d,
        )

# Base Host Strategy (wraps a Config)
class HostStrategy:
    def __init__(self, config: Config):
        self.config = config

    def __repr__(self):
        return f"<HostStrategy id={self.config.id} platform={self.config.platform} role={self.config.role}>"

# Monitoring strategy interfaces
class MonitoringStrategy:
    def subscribe(self, host: Config):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

# Polling implementation - runs a thread that periodically calls a handler
class PollingStrategy(MonitoringStrategy):
    def __init__(self, interval: int, limit: int = 100):
        self.interval = interval
        self.limit = limit
        self._threads: List[threading.Thread] = []
        self._stop_event = threading.Event()

    def subscribe(self, host: Config):
        if not host.polling.get("enabled", False):
            logger.debug("Polling disabled for host %s", host.id)
            return

        t = threading.Thread(target=self._poll_loop, args=(host,), daemon=True)
        t.start()
        self._threads.append(t)
        logger.info("Started polling for host %s every %ss", host.id, self.interval)

    def _poll_loop(self, host: Config):
        # The real implementation should call platform-specific client (GlpiClient, ServiceNowClient, etc.)
        # For now this will call a placeholder sync function.
        while not self._stop_event.is_set():
            try:
                logger.debug("Polling host %s (%s)", host.id, host.endpoint)
                # placeholder: fetch incidents according to host.polling.criteria and handle them
                self._handle_poll(host)
            except Exception as exc:
                logger.exception("Error polling host %s: %s", host.id, exc)
            self._stop_event.wait(self.interval)

    def _handle_poll(self, host: Config):
        # Minimal behavior: log intended action and surface candidate items
        criteria = host.polling.get("criteria", [])
        limit = host.polling.get("limit", self.limit)
        logger.info(
            "Polling %s (%s) with criteria=%s limit=%s",
            host.id,
            host.platform,
            criteria,
            limit,
        )
        # TODO: instantiate per-platform client using host.config.credentials to call APIs
        # Example (pseudocode):
        # client = ClientFactory.create(host.platform, host.credentials, host.endpoint)
        # incidents = client.list_incidents(criteria=criteria, limit=limit)
        # SyncEngine.enqueue(host, incidents)
        # For now just sleep a tiny amount to simulate work
        time.sleep(0.01)

    def stop(self):
        self._stop_event.set()
        for t in self._threads:
            t.join(timeout=1)

# Webhook strategy - placeholder that registers webhook endpoints
class WebhookStrategy(MonitoringStrategy):
    def __init__(self, registry: Dict[str, Config]):
        # registry: path -> host config
        self.registry = registry

    def subscribe(self, host: Config):
        if not host.webhook.get("enabled", False):
            logger.debug("Webhook disabled for host %s", host.id)
            return
        path = host.webhook.get("path", f"/hooks/{host.id}")
        self.registry[path] = host
        logger.info("Registered webhook for host %s at path %s", host.id, path)

    def stop(self):
        self.registry.clear()

# Simple IncidentTracker that wires hosts to strategies
class IncidentTracker:
    def __init__(self, hosts: List[Config]):
        self.hosts = hosts
        self.polling_strategy = None
        self.webhook_registry: Dict[str, Config] = {}
        self.webhook_strategy = WebhookStrategy(self.webhook_registry)
        self.polling_threads: List[threading.Thread] = []

    def start(self):
        # Decide default polling interval from adapter config if present
        default_interval = cfg.get("adapter", {}).get("reconcile_interval", 300)
        # instantiate one shared polling strategy (per-host intervals are used if present)
        self.polling_strategy = PollingStrategy(interval=default_interval)

        for host in self.hosts:
            host_strategy = HostStrategy(host)
            # subscribe webhook if enabled
            self.webhook_strategy.subscribe(host)
            # subscribe polling if enabled with host-specific interval
            if host.polling.get("enabled", False):
                interval = host.polling.get("interval", default_interval)
                # create a dedicated PollingStrategy per host if interval differs
                if interval != self.polling_strategy.interval:
                    ps = PollingStrategy(interval=interval, limit=host.polling.get("limit", 100))
                    ps.subscribe(host)
                else:
                    self.polling_strategy.subscribe(host)

        logger.info("IncidentTracker started: hosts=%s webhook_paths=%s", [h.id for h in self.hosts], list(self.webhook_registry.keys()))

    def stop(self):
        if self.polling_strategy:
            self.polling_strategy.stop()
        self.webhook_strategy.stop()
        logger.info("IncidentTracker stopped")

# Helper to build Config objects from cfg["hosts"]
def build_hosts_from_cfg(cfg: Dict[str, Any]) -> List[Config]:
    hosts_cfg = cfg.get("hosts", [])
    hosts: List[Config] = []
    for h in hosts_cfg:
        try:
            hosts.append(Config.from_dict(h))
        except Exception:
            logger.exception("Failed to parse host config: %s", h)
    return hosts

def main():
    hosts = build_hosts_from_cfg(cfg)
    if not hosts:
        logger.warning("No hosts configured, exiting")
        return
    tracker = IncidentTracker(hosts)
    try:
        tracker.start()
        # Keep main thread alive. In a real service this would be a proper service loop or server.
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down on user request")
    finally:
        tracker.stop()

if __name__ == "__main__":
    main()
#