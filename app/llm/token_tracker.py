"""
F.A.I.T — Token Usage Tracker
Estimates and logs approximate token consumption across all LLM calls.
Uses the industry-standard len(text)/4 heuristic for English text.
"""

import threading
from datetime import datetime, timezone


class TokenTracker:
    """Thread-safe, in-memory token usage tracker."""

    def __init__(self):
        self._lock = threading.Lock()
        self._total_input = 0
        self._total_output = 0
        self._daily_input = 0
        self._daily_output = 0
        self._request_count = 0
        self._current_day = datetime.now(timezone.utc).date()
        self._per_endpoint = {}  # endpoint_name -> {"input": int, "output": int, "calls": int}

    def _reset_if_new_day(self):
        today = datetime.now(timezone.utc).date()
        if today != self._current_day:
            self._daily_input = 0
            self._daily_output = 0
            self._current_day = today

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count using the len/4 heuristic (standard for English text)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    def log_usage(self, endpoint: str, input_text: str, output_text: str):
        """Record token usage for a single LLM call."""
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(output_text)

        with self._lock:
            self._reset_if_new_day()
            self._total_input += input_tokens
            self._total_output += output_tokens
            self._daily_input += input_tokens
            self._daily_output += output_tokens
            self._request_count += 1

            if endpoint not in self._per_endpoint:
                self._per_endpoint[endpoint] = {"input": 0, "output": 0, "calls": 0}
            self._per_endpoint[endpoint]["input"] += input_tokens
            self._per_endpoint[endpoint]["output"] += output_tokens
            self._per_endpoint[endpoint]["calls"] += 1

    def get_stats(self) -> dict:
        """Return current usage statistics."""
        with self._lock:
            self._reset_if_new_day()
            return {
                "today": {
                    "input_tokens": self._daily_input,
                    "output_tokens": self._daily_output,
                    "total_tokens": self._daily_input + self._daily_output,
                },
                "all_time": {
                    "input_tokens": self._total_input,
                    "output_tokens": self._total_output,
                    "total_tokens": self._total_input + self._total_output,
                    "total_requests": self._request_count,
                },
                "per_endpoint": dict(self._per_endpoint),
            }


# Singleton instance
tracker = TokenTracker()
