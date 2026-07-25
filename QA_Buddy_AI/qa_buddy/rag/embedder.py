"""Embedder using fastembed — fully deferred import, all cache paths to /tmp."""

import os
import tempfile

# Pin temp paths before anything else touches ONNX
tempfile.tempdir = "/tmp"
for k in ["TMPDIR", "TEMP", "TMP"]:
    os.environ.setdefault(k, "/tmp")
for k, v in {
    "HF_HOME": "/tmp/hf",
    "HF_HUB_CACHE": "/tmp/hf/hub",
    "XDG_CACHE_HOME": "/tmp/cache",
    "FASTEMP_CACHE": "/tmp/fastembed",
    "SENTENCE_TRANSFORMERS_HOME": "/tmp/st",
    "ORT_TMPDIR": "/tmp/ort",
}.items():
    os.environ.setdefault(k, v)


def _ensure_dirs():
    for d in ["/tmp/hf", "/tmp/hf/hub", "/tmp/cache", "/tmp/fastembed", "/tmp/st", "/tmp/ort"]:
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass  # read-only fs — will be caught at model load


class Embedder:
    def __init__(self):
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        _ensure_dirs()
        from fastembed import TextEmbedding
        self._model = TextEmbedding(
            model_name="BAAI/bge-small-en-v1.5",
            max_length=512,
            cache_dir="/tmp/fastembed",
        )

    def embed(self, text: str) -> list[float]:
        self._load()
        return list(next(self._model.embed(text)))

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._load()
        return [list(v) for v in self._model.embed(texts)]


def embed(text: str) -> list[float]:
    return Embedder().embed(text)


def embed_batch(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return Embedder().embed_batch(texts)
