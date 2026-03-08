from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request


class Ollama:
    def __init__(
        self,
        model: str,
        base_url: str | None = None,
        timeout: int = 120,
    ) -> None:
        self.model = model
        self.base_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or "http://ollama.infra-agent-hub.svc.cluster.local:11434"
        ).rstrip("/")
        self.timeout = timeout

    @staticmethod
    def list_loaded_models(
        *,
        base_url: str | None = None,
        timeout: int = 30,
    ) -> list[str]:
        url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or "http://ollama.infra-agent-hub.svc.cluster.local:11434"
        ).rstrip("/")
        req = request.Request(f"{url}/api/tags", method="GET")
        try:
            with request.urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama HTTP {exc.code}: {details}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Ollama connection error: {exc.reason}") from exc

        models = data.get("models", [])
        return [str(item.get("name")) for item in models if isinstance(item, dict)]

    def _post(
        self,
        path: str,
        payload: dict[str, Any],
        *,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        effective_timeout = timeout if timeout is not None else self.timeout
        try:
            with request.urlopen(req, timeout=effective_timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ollama HTTP {exc.code}: {details}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Ollama connection error: {exc.reason}") from exc

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        stream: bool = False,
        options: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options
        return self._post("/api/generate", payload, timeout=timeout)

    def ask(
        self,
        prompt: str,
        *,
        system: str | None = None,
        options: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> str:
        data = self.generate(
            prompt,
            system=system,
            stream=False,
            options=options,
            timeout=timeout,
        )
        return str(data.get("response", ""))

    def list_models(self) -> list[str]:
        return self.list_loaded_models(base_url=self.base_url, timeout=self.timeout)
