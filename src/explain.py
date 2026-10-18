"""Privacy-safe IBM Granite explanations for TrustPause decisions."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
import json
import logging
import os
from pathlib import Path
import re
import time
from typing import Any, Mapping


LOGGER = logging.getLogger(__name__)
MAX_WORDS = 60

_IDENTIFIER_PATTERNS = (
    re.compile(
        r"\b(?:account|acct|customer|user|sender|receiver|recipient)"
        r"(?:\s+(?:id|number|no))?\s*[:=#-]\s*[A-Za-z0-9][A-Za-z0-9_-]{3,}\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:\+?\d[\d -]{7,}\d)\b"),
    re.compile(r"\b\d{8,}\b"),
)


def _redact_text(value: Any) -> str:
    text = " ".join(str(value).split())
    for pattern in _IDENTIFIER_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def prompt_has_identifiers(prompt: str) -> bool:
    return any(pattern.search(prompt) for pattern in _IDENTIFIER_PATTERNS)


def _limit_words(text: str, limit: int = MAX_WORDS) -> str:
    words = str(text).split()
    if len(words) <= limit:
        return str(text).strip()
    return " ".join(words[:limit]).rstrip(".,;:") + "."


def _normalise_analyst_note(
    text: str,
    fallback: str,
) -> str:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    required = (
        "- Pattern:",
        "- Evidence:",
        "- Suggested action:",
    )

    selected = []

    for label in required:
        match = next(
            (line for line in lines if line.startswith(label)),
            None,
        )
        if match is None:
            return fallback
        selected.append(match)

    return "\n".join(selected)


def _fallback_warning_en(
    decision: str,
    amount_band: str,
) -> str:
    return (
        "Please pause and check the recipient, amount, and reason for this "
        "payment. If anything is unexpected, contact someone you trust and "
        "cancel the transfer if possible."
    )


def _fallback_warning_bm(
    decision: str,
    amount_band: str,
) -> str:
    return (
        "Sila berhenti seketika dan semak penerima, jumlah serta tujuan bayaran "
        "ini. Jika ada yang meragukan, hubungi orang yang dipercayai dan "
        "batalkan pindahan jika masih boleh."
    )


def _fallback_analyst_note(
    decision: str,
    score: float,
    amount_band: str,
    reasons: list[dict[str, str]],
) -> str:
    codes = ", ".join(item["code"] for item in reasons) or "none recorded"

    return "\n".join(
        [
            f"- Pattern: reason codes {codes}.",
            (
                f"- Evidence: decision {decision}, score {score:.2f}, "
                f"amount band {amount_band}."
            ),
            (
                "- Suggested action: review the transfer and pause it if "
                "the evidence is concerning."
            ),
        ]
    )


class GraniteExplainer:
    """Generate explanations with local Granite and safe fallbacks."""

    def __init__(
        self,
        model_path: str | os.PathLike[str] | None = None,
        timeout_seconds: float = 15.0,
        model: Any | None = None,
        n_ctx: int = 16384,
        n_batch: int = 512,
        n_threads: int = 8,
    ) -> None:
        configured_path = model_path or os.getenv("GRANITE_MODEL_PATH")

        self.model_path = (
            Path(configured_path).expanduser()
            if configured_path
            else None
        )

        self.timeout_seconds = float(timeout_seconds)
        self.n_ctx = int(n_ctx)
        self.n_batch = int(n_batch)
        self.n_threads = int(n_threads)
        self.model = model
        self.load_error: str | None = None
        self.last_prompt = ""
        self.last_prompt_has_identifiers = False
        self._prompt_logged = False
        self._executor = ThreadPoolExecutor(max_workers=1)

        if self.model is None:
            self._load_model_once()

    def _load_model_once(self) -> None:
        if self.model_path is None:
            self.load_error = "GRANITE_MODEL_PATH is not set"
            return

        if not self.model_path.is_file():
            self.load_error = (
                f"Granite model not found: {self.model_path}"
            )
            return

        try:
            from llama_cpp import Llama

            self.model = Llama(
                model_path=str(self.model_path),
                n_ctx=self.n_ctx,
                n_batch=self.n_batch,
                n_threads=self.n_threads,
                verbose=False,
            )
        except Exception as exc:
            self.load_error = f"{type(exc).__name__}: {exc}"
            self.model = None

    @staticmethod
    def _normalise_input(
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        reasons = []

        for item in payload.get("reasons", []):
            if not isinstance(item, Mapping):
                continue

            reasons.append(
                {
                    "code": _redact_text(
                        item.get("code", "UNKNOWN")
                    ),
                    "sentence": _redact_text(
                        item.get("sentence", "")
                    ),
                }
            )

        try:
            score = float(payload.get("score", 0.0))
        except (TypeError, ValueError):
            score = 0.0

        return {
            "decision": _redact_text(
                payload.get("decision", "review")
            ),
            "score": score,
            "reasons": reasons,
            "amount_band": _redact_text(
                payload.get("amount_band", "unknown")
            ),
        }

    @staticmethod
    def _make_prompt(
        data: Mapping[str, Any],
        output_kind: str,
    ) -> str:
        reason_text = json.dumps(
            data["reasons"],
            ensure_ascii=False,
            separators=(",", ":"),
        )

        context = (
            f"Decision: {data['decision']}\n"
            f"Risk score: {data['score']:.3f}\n"
            f"Amount band: {data['amount_band']}\n"
            f"Reason codes and explanations: {reason_text}\n"
        )

        instructions = {
            "warning_en": (
                "Write one calm, non-blaming English warning for the sender. "
                "Tell them what to check and that they can cancel the "
                "transfer. Use no more than 60 words."
            ),
            "warning_bm": (
                "Tulis satu amaran ringkas dalam Bahasa Malaysia yang tenang "
                "dan tidak menyalahkan. Beritahu perkara yang perlu disemak "
                "dan bahawa pindahan boleh dibatalkan. Maksimum 60 perkataan."
            ),
            "analyst_note": (
                "Write exactly three short bullet points labelled Pattern, "
                "Evidence, and Suggested action. Use no more than 60 words."
            ),
        }

        examples = {
            "warning_en": (
                "Please pause and check the recipient before continuing."
            ),
            "warning_bm": (
                "Sila berhenti seketika dan semak penerima sebelum meneruskan."
            ),
            "analyst_note": (
                "- Pattern: unusual transfer activity.\n"
                "- Evidence: the supplied risk reasons.\n"
                "- Suggested action: review and pause if needed."
            ),
        }

        return (
            "You explain an existing TrustPause risk decision. "
            "Do not make or change the risk decision. "
            "Use only the supplied information. "
            "Do not invent personal data.\n\n"
            f"{instructions[output_kind]}\n\n"
            "Example:\n"
            "Decision: pause\n"
            "Risk score: 0.80\n"
            "Amount band: medium\n"
            "Reason: unusual transfer pattern\n"
            f"Answer: {examples[output_kind]}\n\n"
            f"{context}"
            "Answer:"
        )

    def _generate_one(
        self,
        prompt: str,
        fallback: str,
    ) -> tuple[str, bool]:
        if self.model is None:
            return fallback, False

        started = time.perf_counter()

        future = self._executor.submit(
            self.model.create_completion,
            prompt=prompt,
            max_tokens=96,
            temperature=0.0,
            stop=["\n\n"],
        )

        try:
            response = future.result(
                timeout=self.timeout_seconds
            )
        except TimeoutError:
            future.cancel()
            return fallback, False
        except Exception as exc:
            LOGGER.warning(
                "Granite generation failed: %s",
                exc,
            )
            return fallback, False

        elapsed = time.perf_counter() - started

        if elapsed > self.timeout_seconds:
            return fallback, False

        try:
            text = response["choices"][0]["text"].strip()
        except (
            KeyError,
            IndexError,
            TypeError,
            AttributeError,
        ):
            return fallback, False

        if not text:
            return fallback, False

        return _limit_words(text), True

    def explain(
        self,
        payload: Mapping[str, Any],
    ) -> dict[str, Any]:
        data = self._normalise_input(payload)

        prompts = {
            key: self._make_prompt(data, key)
            for key in (
                "warning_en",
                "warning_bm",
                "analyst_note",
            )
        }

        combined_prompt = "\n\n".join(prompts.values())
        self.last_prompt = combined_prompt
        self.last_prompt_has_identifiers = (
            prompt_has_identifiers(combined_prompt)
        )

        if not self._prompt_logged:
            LOGGER.info(
                "Granite privacy-audit prompt: %s",
                combined_prompt,
            )
            self._prompt_logged = True

        fallbacks = {
            "warning_en": _fallback_warning_en(
                data["decision"],
                data["amount_band"],
            ),
            "warning_bm": _fallback_warning_bm(
                data["decision"],
                data["amount_band"],
            ),
            "analyst_note": _fallback_analyst_note(
                data["decision"],
                data["score"],
                data["amount_band"],
                data["reasons"],
            ),
        }

        outputs: dict[str, Any] = {}
        timings: dict[str, float] = {}
        used_model = False

        for key, prompt in prompts.items():
            started = time.perf_counter()

            if self.last_prompt_has_identifiers:
                text, generated = fallbacks[key], False
            else:
                text, generated = self._generate_one(
                    prompt,
                    fallbacks[key],
                )

                if key == "analyst_note" and generated:
                    normalised = _normalise_analyst_note(
                        text,
                        fallbacks[key],
                    )

                    if normalised == fallbacks[key]:
                        generated = False

                    text = normalised

            timings[key] = round(
                time.perf_counter() - started,
                4,
            )

            outputs[key] = text
            used_model = used_model or generated

        outputs["generation_seconds"] = timings
        outputs["used_granite"] = used_model
        outputs["prompt_has_identifiers"] = (
            self.last_prompt_has_identifiers
        )
        outputs["model_path"] = (
            str(self.model_path)
            if self.model_path
            else None
        )

        return outputs


_DEFAULT_EXPLAINER: GraniteExplainer | None = None


def explain(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Use one process-wide Granite explainer instance."""
    global _DEFAULT_EXPLAINER

    if _DEFAULT_EXPLAINER is None:
        _DEFAULT_EXPLAINER = GraniteExplainer()

    return _DEFAULT_EXPLAINER.explain(payload)