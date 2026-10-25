#!/usr/bin/env python3
"""
GroqChatbot Generation Module
Image, Video, Music, and Illustration Generation
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
        self.output_dir = "generated"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_image(self, prompt: str, model: str = "flux", **kwargs) -> Dict[str, Any]:
        """Generate images using various providers"""
        try:
            # Try HuggingFace first (free)
            if not self.api_keys.get('huggingface'):
                # Use a free alternative
                return {"success": False, "error": "Add HUGGINGFACE_API_KEY to .env for image generation"}
            
            headers = {"Authorization": f"Bearer {self.api_keys['huggingface']}"}
            
            if model == "flux":
                API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
            elif model == "sdxl":
                API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
            elif model == "sd15":
                API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
            else:
                API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
            
            response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
            
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
                    "model": model
                }
            else:
                return {"success": False, "error": f"API error: {response.status_code} - {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def generate_illustration(self, prompt: str, style: str = "digital art") -> Dict[str, Any]:
        enhanced_prompt = f"{style}, illustration: {prompt}, high quality, detailed"
        return self.generate_image(enhanced_prompt, model="flux")
    
    def generate_music(self, prompt: str, duration: int = 30, model: str = "musicgen") -> Dict[str, Any]:
        """Generate music using MusicGen via HuggingFace"""
        try:
            if not self.api_keys.get('huggingface'):
                return {"success": False, "error": "Add HUGGINGFACE_API_KEY to .env for music generation"}
            
            headers = {"Authorization": f"Bearer {self.api_keys['huggingface']}"}
            
            if model == "musicgen":
                API_URL = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
            elif model == "musicgen-medium":
                API_URL = "https://api-inference.huggingface.co/models/facebook/musicgen-medium"
            elif model == "audiogen":
                API_URL = "https://api-inference.huggingface.co/models/facebook/audiogen-medium"
            else:
                API_URL = "https://api-inference.huggingface.co/models/facebook/musicgen-small"
            
            response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
            
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
                    "duration": duration
                }
            elif response.status_code == 503:
                return {"success": False, "error": "Model is loading, please try again in a few minutes"}
            else:
                return {"success": False, "error": f"API error: {response.status_code} - {response.text[:200]}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
            "image": ["flux", "sdxl", "sd15"],
            "illustration": ["flux"],
            "music": ["musicgen", "musicgen-medium", "audiogen"],
            "video": ["hunyuan", "cogvideo"],
            "animation": ["animatediff"]
        }

if __name__ == "__main__":
    gen = GenerationEngine()
    print(json.dumps(gen.get_supported_models(), indent=2))
