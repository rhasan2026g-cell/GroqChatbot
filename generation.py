#!/usr/bin/env python3
"""GroqChatbot creation studio.

Image, illustration, music and video generation through several providers.
Every provider is optional: the engine reports exactly what is configured and
returns actionable errors instead of pretending a request succeeded.
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app_paths import GENERATED_DIR, ensure_dirs

try:
    import requests
except ImportError:  # pragma: no cover - requests is a hard dependency in requirements
    requests = None

HF_ROUTER = "https://router.huggingface.co/hf-inference/models"
HF_LEGACY = "https://api-inference.huggingface.co/models"
REPLICATE_API = "https://api.replicate.com/v1"

IMAGE_MODELS = {
    "flux-schnell": {
        "label": "FLUX.1 Schnell · fastest",
        "hf": "black-forest-labs/FLUX.1-schnell",
        "replicate": "black-forest-labs/flux-schnell",
        "fal": "fal-ai/flux/schnell",
    },
    "flux-dev": {
        "label": "FLUX.1 Dev · quality",
        "hf": "black-forest-labs/FLUX.1-dev",
        "replicate": "black-forest-labs/flux-dev",
        "fal": "fal-ai/flux/dev",
    },
    "sdxl": {
        "label": "Stable Diffusion XL",
        "hf": "stabilityai/stable-diffusion-xl-base-1.0",
        "replicate": "stability-ai/sdxl",
        "fal": "fal-ai/fast-sdxl",
    },
    "sd15": {
        "label": "Stable Diffusion 1.5 · classic",
        "hf": "runwayml/stable-diffusion-v1-5",
        "replicate": "stability-ai/stable-diffusion",
        "fal": "fal-ai/fast-sdxl",
    },
}

MUSIC_MODELS = {
    "musicgen-small": {
        "label": "MusicGen Small · fast",
        "hf": "facebook/musicgen-small",
        "replicate": "meta/musicgen",
    },
    "musicgen-medium": {
        "label": "MusicGen Medium · balanced",
        "hf": "facebook/musicgen-medium",
        "replicate": "meta/musicgen",
    },
    "musicgen-large": {
        "label": "MusicGen Large · richest",
        "hf": "facebook/musicgen-large",
        "replicate": "meta/musicgen",
    },
    "audiogen": {
        "label": "AudioGen · sound effects",
        "hf": "facebook/audiogen-medium",
        "replicate": "meta/audiogen",
    },
}

VIDEO_MODELS = {
    "hunyuan": {"label": "Hunyuan Video", "replicate": "tencent/hunyuan-video", "fal": "fal-ai/hunyuan-video"},
    "cogvideo": {"label": "CogVideoX 5B", "replicate": "lucataco/cogvideox-5b", "fal": "fal-ai/cogvideox-5b"},
    "minimax": {"label": "MiniMax Video-01", "replicate": "minimax/video-01", "fal": "fal-ai/minimax-video"},
}


def _safe_slug(text: str, limit: int = 42) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", text.strip().lower()).strip("-")
    return (slug or "creation")[:limit]


class GenerationEngine:
    """Provider-aware generation with graceful fallbacks."""

    def __init__(self, api_keys: Optional[Dict[str, str]] = None, output_dir: Optional[str] = None):
        ensure_dirs()
        self.api_keys = {
            "huggingface": os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN") or "",
            "replicate": os.getenv("REPLICATE_API_TOKEN") or "",
            "stability": os.getenv("STABILITY_API_KEY") or "",
            "fal": os.getenv("FAL_KEY") or "",
            "together": os.getenv("TOGETHER_API_KEY") or "",
            "openrouter": os.getenv("OPENROUTER_API_KEY") or "",
        }
        for key, value in (api_keys or {}).items():
            if value:
                self.api_keys[key] = value
        self.api_keys = {k: (v or "").strip() for k, v in self.api_keys.items()}
        self.output_dir = str(output_dir or GENERATED_DIR)
        os.makedirs(self.output_dir, exist_ok=True)

    # ------------------------------------------------------------ providers
    def provider_status(self) -> Dict[str, Dict[str, Any]]:
        labels = {
            "huggingface": "HuggingFace Inference",
            "replicate": "Replicate",
            "stability": "Stability AI",
            "fal": "fal.ai",
            "together": "Together AI",
            "openrouter": "OpenRouter",
        }
        return {
            key: {"label": labels[key], "configured": bool(value)}
            for key, value in self.api_keys.items()
        }

    def configured_providers(self) -> List[str]:
        return [k for k, v in self.api_keys.items() if v]

    def _missing_error(self, kind: str) -> Dict[str, Any]:
        return {
            "success": False,
            "error": (
                f"{kind} generation needs at least one provider key. "
                "Add HuggingFace, Replicate, Stability AI or fal.ai in Settings → API keys."
            ),
        }

    @staticmethod
    def _requests_ready() -> bool:
        return requests is not None

    # --------------------------------------------------------------- images
    def generate_image(
        self,
        prompt: str,
        model: str = "flux-schnell",
        width: int = 1024,
        height: int = 1024,
        negative_prompt: str = "",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        if not prompt:
            return {"success": False, "error": "Write a prompt first."}
        if not self._requests_ready():
            return {"success": False, "error": "The requests package is missing."}
        spec = IMAGE_MODELS.get(model, IMAGE_MODELS["flux-schnell"])
        errors: List[str] = []
        started = time.time()

        for provider, fn in (
            ("huggingface", self._image_huggingface),
            ("replicate", self._image_replicate),
            ("stability", self._image_stability),
            ("fal", self._image_fal),
            ("together", self._image_together),
        ):
            if not self.api_keys.get(provider):
                continue
            try:
                result = fn(prompt, spec, width, height, negative_prompt)
                if result.get("success"):
                    result.update({"prompt": prompt, "model": model, "provider": provider})
                    result["elapsed"] = round(time.time() - started, 1)
                    self._write_metadata(result)
                    return result
                if result.get("error"):
                    errors.append(f"{provider}: {result['error']}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{provider}: {exc}")
        if errors:
            return {"success": False, "error": " | ".join(errors[:4])}
        return self._missing_error("Image")

    def _save(self, data: bytes, kind: str, prompt: str, extension: str) -> Dict[str, Any]:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{kind}_{stamp}_{_safe_slug(prompt)}.{extension}"
        path = Path(self.output_dir) / filename
        path.write_bytes(data)
        return {
            "success": True,
            "type": kind,
            "filepath": str(path),
            "filename": filename,
            "bytes": len(data),
        }

    def _http_error(self, response: "requests.Response") -> str:
        try:
            payload = response.json()
            if isinstance(payload, dict):
                message = payload.get("error") or payload.get("message") or payload.get("detail")
                if isinstance(message, dict):
                    message = message.get("message") or json.dumps(message)
                if message:
                    return f"HTTP {response.status_code}: {str(message)[:220]}"
        except Exception:
            pass
        text = (response.text or "").strip().replace("\n", " ")
        return f"HTTP {response.status_code}: {text[:220] or 'no details'}"

    def _image_huggingface(
        self, prompt: str, spec: dict, width: int, height: int, negative: str
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_keys['huggingface']}",
            "Accept": "image/png",
        }
        params = {
            "width": int(width),
            "height": int(height),
        }
        if negative:
            params["negative_prompt"] = negative
        last_error = ""
        for base in (HF_ROUTER, HF_LEGACY):
            url = f"{base}/{spec['hf']}"
            for attempt in range(2):
                response = requests.post(
                    url, headers=headers, params=params,
                    json={"inputs": prompt}, timeout=180,
                )
                if response.status_code == 200 and response.content:
                    ctype = response.headers.get("content-type", "")
                    if "application/json" in ctype:
                        last_error = self._http_error(response)
                        continue
                    return self._save(response.content, "image", prompt, "png")
                if response.status_code == 503:
                    last_error = "model is loading on HuggingFace — try again shortly"
                    time.sleep(2 if attempt == 0 else 0)
                    continue
                last_error = self._http_error(response)
                break
        return {"success": False, "error": last_error or "HuggingFace request failed"}

    def _image_replicate(
        self, prompt: str, spec: dict, width: int, height: int, negative: str
    ) -> Dict[str, Any]:
        payload = {
            "prompt": prompt,
            "width": int(width),
            "height": int(height),
            "num_outputs": 1,
        }
        if negative:
            payload["negative_prompt"] = negative
        result = self._replicate_run(spec["replicate"], payload, timeout=240)
        if not result.get("success"):
            return result
        url = result.get("url")
        if not url:
            return {"success": False, "error": "Replicate returned no image URL"}
        image = requests.get(url, timeout=120)
        if image.status_code != 200:
            return {"success": False, "error": self._http_error(image)}
        return self._save(image.content, "image", prompt, "png")

    def _image_stability(
        self, prompt: str, spec: dict, width: int, height: int, negative: str
    ) -> Dict[str, Any]:
        endpoint = "https://api.stability.ai/v2beta/stable-image/generate/core"
        headers = {
            "Authorization": f"Bearer {self.api_keys['stability']}",
            "Accept": "image/*",
        }
        files = {"prompt": (None, prompt), "output_format": (None, "png")}
        if negative:
            files["negative_prompt"] = (None, negative)
        response = requests.post(endpoint, headers=headers, files=files, timeout=180)
        if response.status_code == 200 and response.content:
            return self._save(response.content, "image", prompt, "png")
        return {"success": False, "error": self._http_error(response)}

    def _image_fal(
        self, prompt: str, spec: dict, width: int, height: int, negative: str
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Key {self.api_keys['fal']}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
            "image_size": {"width": int(width), "height": int(height)},
            "num_images": 1,
        }
        if negative:
            payload["negative_prompt"] = negative
        response = requests.post(
            f"https://fal.run/{spec['fal']}", headers=headers, json=payload, timeout=240
        )
        if response.status_code != 200:
            return {"success": False, "error": self._http_error(response)}
        data = response.json()
        images = data.get("images") or []
        if not images:
            return {"success": False, "error": "fal.ai returned no images"}
        url = images[0].get("url")
        image = requests.get(url, timeout=120)
        if image.status_code != 200:
            return {"success": False, "error": self._http_error(image)}
        return self._save(image.content, "image", prompt, "png")

    def _image_together(
        self, prompt: str, spec: dict, width: int, height: int, negative: str
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_keys['together']}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell-Free",
            "prompt": prompt,
            "width": int(width),
            "height": int(height),
            "steps": 4,
            "n": 1,
            "response_format": "b64_json",
        }
        response = requests.post(
            "https://api.together.xyz/v1/images/generations",
            headers=headers, json=payload, timeout=240,
        )
        if response.status_code != 200:
            return {"success": False, "error": self._http_error(response)}
        data = response.json().get("data") or []
        if not data:
            return {"success": False, "error": "Together returned no images"}
        item = data[0]
        if item.get("b64_json"):
            return self._save(base64.b64decode(item["b64_json"]), "image", prompt, "png")
        if item.get("url"):
            image = requests.get(item["url"], timeout=120)
            if image.status_code == 200:
                return self._save(image.content, "image", prompt, "png")
        return {"success": False, "error": "Together returned an unusable response"}

    def generate_illustration(
        self, prompt: str, style: str = "digital art", model: str = "flux-schnell", **kwargs: Any
    ) -> Dict[str, Any]:
        styled = (
            f"{style} illustration of {prompt}. Rich colour, crisp shapes, "
            "professional composition, high detail, no text."
        )
        result = self.generate_image(styled, model=model, **kwargs)
        if result.get("success"):
            result["type"] = "illustration"
        return result

    # ---------------------------------------------------------------- music
    def generate_music(
        self, prompt: str, duration: int = 30, model: str = "musicgen-small", **kwargs: Any
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        if not prompt:
            return {"success": False, "error": "Describe the music first."}
        if not self._requests_ready():
            return {"success": False, "error": "The requests package is missing."}
        spec = MUSIC_MODELS.get(model, MUSIC_MODELS["musicgen-small"])
        duration = max(5, min(int(duration), 60))
        errors: List[str] = []
        started = time.time()

        if self.api_keys.get("huggingface"):
            try:
                result = self._music_huggingface(prompt, spec)
                if result.get("success"):
                    result.update({
                        "prompt": prompt, "model": model, "provider": "huggingface",
                        "duration": duration, "elapsed": round(time.time() - started, 1),
                    })
                    self._write_metadata(result)
                    return result
                errors.append(f"huggingface: {result.get('error')}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"huggingface: {exc}")

        if self.api_keys.get("replicate"):
            try:
                result = self._music_replicate(prompt, spec, duration)
                if result.get("success"):
                    result.update({
                        "prompt": prompt, "model": model, "provider": "replicate",
                        "duration": duration, "elapsed": round(time.time() - started, 1),
                    })
                    self._write_metadata(result)
                    return result
                errors.append(f"replicate: {result.get('error')}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"replicate: {exc}")

        if errors:
            return {"success": False, "error": " | ".join(errors[:3])}
        return self._missing_error("Music")

    def _music_huggingface(self, prompt: str, spec: dict) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_keys['huggingface']}"}
        last_error = ""
        for base in (HF_ROUTER, HF_LEGACY):
            url = f"{base}/{spec['hf']}"
            for attempt in range(2):
                response = requests.post(
                    url, headers=headers, json={"inputs": prompt}, timeout=300
                )
                if response.status_code == 200 and response.content:
                    ctype = response.headers.get("content-type", "")
                    if "application/json" in ctype:
                        last_error = self._http_error(response)
                        continue
                    ext = "wav" if "wav" in ctype or b"RIFF" == response.content[:4] else "mp3"
                    return self._save(response.content, "music", prompt, ext)
                if response.status_code == 503:
                    last_error = "model is loading on HuggingFace — try again shortly"
                    time.sleep(2 if attempt == 0 else 0)
                    continue
                last_error = self._http_error(response)
                break
        return {"success": False, "error": last_error or "HuggingFace request failed"}

    def _music_replicate(self, prompt: str, spec: dict, duration: int) -> Dict[str, Any]:
        payload = {
            "prompt": prompt,
            "duration": max(8, min(int(duration), 30)),
            "model_version": "stereo-large" if "large" in spec["hf"] else "stereo-melody-large",
            "output_format": "wav",
        }
        result = self._replicate_run(spec["replicate"], payload, timeout=300)
        if not result.get("success"):
            return result
        url = result.get("url")
        if not url:
            return {"success": False, "error": "Replicate returned no audio URL"}
        audio = requests.get(url, timeout=120)
        if audio.status_code != 200:
            return {"success": False, "error": self._http_error(audio)}
        return self._save(audio.content, "music", prompt, "wav")

    # ---------------------------------------------------------------- video
    def generate_video(
        self, prompt: str, duration: int = 5, model: str = "hunyuan", **kwargs: Any
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        if not prompt:
            return {"success": False, "error": "Describe the video first."}
        if not self._requests_ready():
            return {"success": False, "error": "The requests package is missing."}
        spec = VIDEO_MODELS.get(model, VIDEO_MODELS["hunyuan"])
        errors: List[str] = []
        started = time.time()

        if self.api_keys.get("replicate"):
            try:
                result = self._replicate_run(
                    spec["replicate"],
                    {"prompt": prompt, "duration": max(3, min(int(duration), 10))},
                    timeout=600,
                )
                if result.get("success") and result.get("url"):
                    video = requests.get(result["url"], timeout=300)
                    if video.status_code == 200:
                        saved = self._save(video.content, "video", prompt, "mp4")
                        saved.update({
                            "prompt": prompt, "model": model, "provider": "replicate",
                            "duration": duration, "elapsed": round(time.time() - started, 1),
                        })
                        self._write_metadata(saved)
                        return saved
                    errors.append(f"replicate download: {self._http_error(video)}")
                else:
                    errors.append(f"replicate: {result.get('error')}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"replicate: {exc}")

        if self.api_keys.get("fal"):
            try:
                headers = {
                    "Authorization": f"Key {self.api_keys['fal']}",
                    "Content-Type": "application/json",
                }
                response = requests.post(
                    f"https://fal.run/{spec['fal']}",
                    headers=headers,
                    json={"prompt": prompt},
                    timeout=600,
                )
                if response.status_code == 200:
                    data = response.json()
                    url = (data.get("video") or {}).get("url") or data.get("url")
                    if url:
                        video = requests.get(url, timeout=300)
                        if video.status_code == 200:
                            saved = self._save(video.content, "video", prompt, "mp4")
                            saved.update({
                                "prompt": prompt, "model": model, "provider": "fal",
                                "duration": duration, "elapsed": round(time.time() - started, 1),
                            })
                            self._write_metadata(saved)
                            return saved
                    errors.append("fal: no video URL in response")
                else:
                    errors.append(f"fal: {self._http_error(response)}")
            except Exception as exc:  # noqa: BLE001
                errors.append(f"fal: {exc}")

        if errors:
            return {"success": False, "error": " | ".join(errors[:3])}
        return self._missing_error("Video")

    def generate_animation(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        return self.generate_video(prompt, duration=3, **kwargs)

    # ----------------------------------------------------------- replicate
    def _replicate_run(self, model: str, payload: Dict[str, Any], timeout: int = 300) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_keys['replicate']}",
            "Content-Type": "application/json",
            "Prefer": "wait=60",
        }
        response = requests.post(
            f"{REPLICATE_API}/models/{model}/predictions",
            headers=headers,
            json={"input": payload},
            timeout=90,
        )
        if response.status_code not in (200, 201):
            return {"success": False, "error": self._http_error(response)}
        data = response.json()
        deadline = time.time() + timeout
        while data.get("status") in ("starting", "processing", "queued"):
            if time.time() > deadline:
                return {"success": False, "error": "Replicate timed out"}
            time.sleep(2.5)
            get_url = data.get("urls", {}).get("get")
            if not get_url:
                return {"success": False, "error": "Replicate returned no polling URL"}
            poll = requests.get(get_url, headers=headers, timeout=60)
            if poll.status_code != 200:
                return {"success": False, "error": self._http_error(poll)}
            data = poll.json()
        if data.get("status") not in ("succeeded", "successful"):
            return {
                "success": False,
                "error": f"Replicate status: {data.get('status')} {str(data.get('error'))[:200]}",
            }
        output = data.get("output")
        url = ""
        if isinstance(output, str):
            url = output
        elif isinstance(output, list) and output:
            first = output[0]
            url = first if isinstance(first, str) else str(first.get("url", ""))
        elif isinstance(output, dict):
            url = output.get("url", "")
        if not url:
            return {"success": False, "error": "Replicate returned no output"}
        return {"success": True, "url": url, "raw": data}

    # ------------------------------------------------------------ plumbing
    def _write_metadata(self, result: Dict[str, Any]) -> None:
        try:
            path = result.get("filepath")
            if not path:
                return
            meta_path = Path(path).with_suffix(Path(path).suffix + ".json")
            meta = {k: v for k, v in result.items() if k not in ("raw",)}
            meta["created"] = datetime.now().isoformat(timespec="seconds")
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def get_supported_models(self) -> Dict[str, List[str]]:
        return {
            "image": list(IMAGE_MODELS),
            "illustration": list(IMAGE_MODELS),
            "music": list(MUSIC_MODELS),
            "video": list(VIDEO_MODELS),
            "animation": list(VIDEO_MODELS),
        }

    def model_labels(self, kind: str) -> Dict[str, str]:
        mapping = {
            "image": IMAGE_MODELS,
            "illustration": IMAGE_MODELS,
            "music": MUSIC_MODELS,
            "video": VIDEO_MODELS,
            "animation": VIDEO_MODELS,
        }.get(kind, IMAGE_MODELS)
        return {key: value["label"] for key, value in mapping.items()}


if __name__ == "__main__":
    gen = GenerationEngine()
    print(json.dumps(gen.provider_status(), indent=2))
    print(json.dumps(gen.get_supported_models(), indent=2))
