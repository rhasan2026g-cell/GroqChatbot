#!/usr/bin/env python3
"""
GroqChatbot Generation Module
Multi-Provider Image, Video, Music, and Illustration Generation
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import base64

class GenerationEngine:
    def __init__(self, api_keys: Dict[str, str] = None):
        self.api_keys = api_keys or {}
        # Also check environment variables
        self.api_keys.update({
            'huggingface': os.getenv('HUGGINGFACE_API_KEY') or self.api_keys.get('huggingface'),
            'replicate': os.getenv('REPLICATE_API_TOKEN') or self.api_keys.get('replicate'),
            'stability': os.getenv('STABILITY_API_KEY') or self.api_keys.get('stability'),
            'openrouter': os.getenv('OPENROUTER_API_KEY') or self.api_keys.get('openrouter'),
            'fal': os.getenv('FAL_KEY') or self.api_keys.get('fal'),
            'together': os.getenv('TOGETHER_API_KEY') or self.api_keys.get('together'),
        })
        self.output_dir = "generated"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_image(self, prompt: str, model: str = "flux", **kwargs) -> Dict[str, Any]:
        """Generate images using multiple providers"""
        # Try providers in order of preference
        providers = [
            self._generate_image_huggingface,
            self._generate_image_replicate,
            self._generate_image_stability,
        ]
        
        for provider in providers:
            try:
                result = provider(prompt, model, **kwargs)
                if result.get('success'):
                    return result
            except Exception as e:
                continue
        
        return {"success": False, "error": "All image generation providers failed. Add API keys for HuggingFace, Replicate, or Stability AI."}
    
    def _generate_image_huggingface(self, prompt: str, model: str = "flux", **kwargs) -> Dict[str, Any]:
        if not self.api_keys.get('huggingface'):
            return {"success": False, "error": "No HF key"}
        
        headers = {"Authorization": f"Bearer {self.api_keys['huggingface']}"}
        
        if model == "flux" or model == "flux-dev":
            API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
        elif model == "flux-schnell":
            API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        elif model == "sdxl":
            API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        elif model == "sd15":
            API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
        elif model == "realisrgan":
            API_URL = "https://api-inference.huggingface.co/models/CompVis/stable-diffusion-v1-4"
        else:
            API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
        
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=120)
        
        if response.status_code == 200:
            filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return {
                "success": True,
                "type": "image",
                "filepath": filepath,
                "filename": filename,
                "prompt": prompt,
                "model": model,
                "provider": "huggingface"
            }
        elif response.status_code == 503:
            return {"success": False, "error": "Model loading"}
        else:
            return {"success": False, "error": f"HF error: {response.status_code}"}
    
    def _generate_image_replicate(self, prompt: str, model: str = "flux", **kwargs) -> Dict[str, Any]:
        if not self.api_keys.get('replicate'):
            return {"success": False, "error": "No Replicate key"}
        return {"success": False, "error": "Replicate integration pending"}
    
    def _generate_image_stability(self, prompt: str, model: str = "flux", **kwargs) -> Dict[str, Any]:
        if not self.api_keys.get('stability'):
            return {"success": False, "error": "No Stability key"}
        return {"success": False, "error": "Stability integration pending"}
    
    def generate_illustration(self, prompt: str, style: str = "digital art") -> Dict[str, Any]:
        enhanced_prompt = f"{style}, illustration: {prompt}, high quality, detailed"
        return self.generate_image(enhanced_prompt, model="flux")
    
    def generate_music(self, prompt: str, duration: int = 30, model: str = "musicgen") -> Dict[str, Any]:
        """Generate music using multiple providers"""
        providers = [
            self._generate_music_huggingface,
        ]
        
        for provider in providers:
            try:
                result = provider(prompt, duration, model)
                if result.get('success'):
                    return result
            except Exception as e:
                continue
        
        return {"success": False, "error": "Music generation requires HUGGINGFACE_API_KEY. Get free key at https://huggingface.co/settings/tokens"}
    
    def _generate_music_huggingface(self, prompt: str, duration: int = 30, model: str = "musicgen") -> Dict[str, Any]:
        if not self.api_keys.get('huggingface'):
            return {"success": False, "error": "No HF key"}
        
        headers = {"Authorization": f"Bearer {self.api_keys['huggingface']}"}
        
        if model == "musicgen":
            API_URL = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
        elif model == "musicgen-medium":
            API_URL = "https://api-inference.huggingface.co/models/facebook/musicgen-medium"
        elif model == "musicgen-large":
            API_URL = "https://api-inference.huggingface.co/models/facebook/musicgen-large"
        elif model == "audiogen":
            API_URL = "https://api-inference.huggingface.co/models/facebook/audiogen-medium"
        else:
            API_URL = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
        
        response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=300)
        
        if response.status_code == 200:
            filename = f"music_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return {
                "success": True,
                "type": "music",
                "filepath": filepath,
                "filename": filename,
                "prompt": prompt,
                "model": model,
                "duration": duration,
                "provider": "huggingface"
            }
        elif response.status_code == 503:
            return {"success": False, "error": "Model loading, retry in 2-5 minutes"}
        else:
            return {"success": False, "error": f"HF error: {response.status_code}"}
    
    def generate_video(self, prompt: str, duration: int = 5, model: str = "hunyuan") -> Dict[str, Any]:
        """Generate video using AI models"""
        try:
            if not self.api_keys.get('huggingface') and not self.api_keys.get('replicate'):
                return {"success": False, "error": "Add HUGGINGFACE_API_KEY or REPLICATE_API_TOKEN for video generation"}
            
            # Try HuggingFace first
            if self.api_keys.get('huggingface'):
                headers = {"Authorization": f"Bearer {self.api_keys['huggingface']}"}
                if model == "hunyuan":
                    API_URL = "https://api-inference.huggingface.co/models/tencent/HunyuanVideo"
                elif model == "cogvideo":
                    API_URL = "https://api-inference.huggingface.co/models/THUDM/CogVideoX-5b"
                else:
                    API_URL = "https://api-inference.huggingface.co/models/tencent/HunyuanVideo"
                
                response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
                
                if response.status_code == 200:
                    filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                    filepath = os.path.join(self.output_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    return {
                        "success": True,
                        "type": "video",
                        "filepath": filepath,
                        "filename": filename,
                        "prompt": prompt,
                        "model": model,
                        "duration": duration
                    }
                elif response.status_code == 503:
                    return {"success": False, "error": "Model is loading, please try again in a few minutes"}
                else:
                    return {"success": False, "error": f"API error: {response.status_code}"}
            
            return {"success": False, "error": "Video generation requires model to be available"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_animation(self, prompt: str) -> Dict[str, Any]:
        return self.generate_video(prompt, duration=3)
    
    def get_supported_models(self) -> Dict[str, List[str]]:
        return {
            "image": ["flux", "flux-dev", "flux-schnell", "sdxl", "sd15"],
            "illustration": ["flux", "flux-dev"],
            "music": ["musicgen", "musicgen-medium", "musicgen-large", "audiogen"],
            "video": ["hunyuan", "cogvideo"],
            "animation": ["animatediff"]
        }

if __name__ == "__main__":
    gen = GenerationEngine()
    print(json.dumps(gen.get_supported_models(), indent=2))
