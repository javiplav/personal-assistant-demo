# circuit_breaker.py
import time
from dataclasses import dataclass
from typing import Dict

@dataclass
class BreakerConfig:
    """Configuration for circuit breaker behavior"""
    window_seconds: int = 300        # 5 minutes rolling window
    buckets: int = 10                # 30s each bucket  
    min_requests: int = 50           # Minimum requests before breaking
    failure_threshold: float = 0.7   # 70% failure rate threshold
    cooldown_seconds: int = 60       # Cool-down period before half-open

class CircuitBreaker:
    """Hystrix-style circuit breaker with rolling window failure tracking"""
    
    CLOSED = "closed"
    OPEN = "open" 
    HALF_OPEN = "half_open"

    def __init__(self, cfg: BreakerConfig):
        self.cfg = cfg
        self.bucket_len = cfg.window_seconds / cfg.buckets
        self.buckets = [{"s": 0, "f": 0, "t": time.time()} for _ in range(cfg.buckets)]
        self.state = self.CLOSED
        self.open_since = 0.0

    def _idx(self, now: float) -> int:
        """Calculate bucket index for given timestamp"""
        return int(now / self.bucket_len) % self.cfg.buckets

    def _rotate(self, now: float):
        """Rotate bucket if enough time has passed"""
        idx = self._idx(now)
        b = self.buckets[idx]
        if now - b["t"] >= self.bucket_len:
            self.buckets[idx] = {"s": 0, "f": 0, "t": now}

    def allow(self) -> bool:
        """Check if request should be allowed through the circuit breaker"""
        now = time.time()
        self._rotate(now)
        
        if self.state == self.OPEN:
            if now - self.open_since >= self.cfg.cooldown_seconds:
                self.state = self.HALF_OPEN
                return True  # allow a probe
            return False
        return True

    def on_result(self, ok: bool):
        """Record the result of a request (success or failure)"""
        now = time.time()
        self._rotate(now)
        idx = self._idx(now)
        
        if ok: 
            self.buckets[idx]["s"] += 1
        else:  
            self.buckets[idx]["f"] += 1

        # Compute window totals
        s = sum(b["s"] for b in self.buckets)
        f = sum(b["f"] for b in self.buckets) 
        total = s + f

        if self.state in (self.CLOSED, self.HALF_OPEN):
            if total >= self.cfg.min_requests and f / max(total, 1) >= self.cfg.failure_threshold:
                self.state = self.OPEN
                self.open_since = now
        elif self.state == self.OPEN:
            # Should not record normally in OPEN state; but if HALF_OPEN probe:
            pass

        # Handle half-open probe result
        if self.state == self.HALF_OPEN:
            if ok:
                # Success → close completely (reset)
                self.state = self.CLOSED
                self.buckets = [{"s": 0, "f": 0, "t": now} for _ in range(self.cfg.buckets)]
            else:
                self.state = self.OPEN
                self.open_since = now

    def get_state(self) -> str:
        """Get current circuit breaker state"""
        return self.state
    
    def get_metrics(self) -> Dict:
        """Get current circuit breaker metrics"""
        s = sum(b["s"] for b in self.buckets)
        f = sum(b["f"] for b in self.buckets)
        total = s + f
        failure_rate = f / max(total, 1) if total > 0 else 0.0
        
        return {
            "state": self.state,
            "total_requests": total,
            "success_count": s,
            "failure_count": f,
            "failure_rate": failure_rate,
            "open_since": self.open_since if self.state == self.OPEN else None
        }


class ToolCircuitBreakerRegistry:
    """Registry managing circuit breakers per tool"""
    
    def __init__(self, default_config: BreakerConfig = None):
        self.default_config = default_config or BreakerConfig()
        self.breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, tool_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a tool"""
        if tool_name not in self.breakers:
            self.breakers[tool_name] = CircuitBreaker(self.default_config)
        return self.breakers[tool_name]
    
    def allow_request(self, tool_name: str) -> bool:
        """Check if request to tool should be allowed"""
        return self.get_breaker(tool_name).allow()
    
    def record_result(self, tool_name: str, success: bool):
        """Record result for a tool call"""
        self.get_breaker(tool_name).on_result(success)
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """Get metrics for all tools"""
        return {tool: breaker.get_metrics() for tool, breaker in self.breakers.items()}
    
    def reset_breaker(self, tool_name: str):
        """Reset a specific tool's circuit breaker"""
        if tool_name in self.breakers:
            del self.breakers[tool_name]
