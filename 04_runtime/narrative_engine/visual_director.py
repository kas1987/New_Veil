import json
import logging
import os
import random
import threading
import urllib.error
import urllib.request
from pathlib import Path

logger = logging.getLogger("VisualDirector")

COMFY_URL = "http://127.0.0.1:8188"


class VisualDirector:
    def __init__(self, workflow_template_path: str = None):
        self.workflow_path = workflow_template_path

    def _post_to_comfy(self, prompt_workflow: dict):
        try:
            data = json.dumps({"prompt": prompt_workflow, "client_id": "narrative-engine"}).encode("utf-8")
            req = urllib.request.Request(
                f"{COMFY_URL}/prompt", data=data, headers={"Content-Type": "application/json"}, method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                prompt_id = result.get("prompt_id")
                logger.info(f"✅ [Async Worker] ComfyUI Job queued: {prompt_id}. Generating in background...")
        except TimeoutError:
            logger.error("❌ [Async Worker] ComfyUI connection timed out.")
        except urllib.error.URLError as e:
            logger.error(f"❌ [Async Worker] ComfyUI connection failed: {e}.")

    def generate_image_from_state(self, current_state, llm_response: str, target_model: str):
        logger.info(f"🎨 VisualDirector: Constructing HQ Scene for {target_model}...")

        base_prompt = f"score_9, score_8_up, score_7_up, (photorealistic:1.3), (highly detailed:1.2), ultra high definition, 8k, masterpiece, RAW photo, 1girl, {target_model} lookalike, detailed skin texture, soft studio lighting, cinematic framing"

        modifiers = []
        if current_state.arousal > 70:
            modifiers.extend(
                ["(flushed skin:1.3)", "(heavy breathing:1.2)", "parted lips", "(messy hair:1.2)", "sweat glistening"]
            )
        elif current_state.intimacy > 60:
            modifiers.extend(["soft lighting", "gentle smile", "intimate framing", "eye contact"])
        if current_state.inhibition < 30:
            modifiers.append("submissive posture")

        final_positive_prompt = f"{base_prompt}, {', '.join(modifiers)}"
        final_negative_prompt = "score_4, score_5, score_6, (blurry:1.3), (low quality:1.3), (distorted:1.3), (deformed:1.3), bad anatomy, watermark, text, signature, lowres, monochrome"
        logger.info(f"--> Injected Prompt: {final_positive_prompt}")

        try:
            faces_root = Path(os.environ.get("VEIL_REACTOR_FACES", "ReActor_Faces"))
            model_dir = faces_root / target_model.lower().replace(" ", "_")
            reference_images = os.listdir(model_dir)
            random_face = f"{model_dir.as_posix()}/" + random.choice(reference_images)
        except Exception:
            # Fallback
            random_face = "ReActor_Faces/autumn_falls/Autumn_Falls_profile.jpg"

        mock_workflow = {
            "1": {
                "inputs": {"ckpt_name": ".01_Best\\uberRealisticPornMergePonyxl_ponyxlHybridV1.safetensors"},
                "class_type": "CheckpointLoaderSimple",
            },
            "2": {"inputs": {"text": f"{final_positive_prompt}", "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
            "3": {"inputs": {"text": final_negative_prompt, "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
            "4": {"inputs": {"width": 1024, "height": 1024, "batch_size": 1}, "class_type": "EmptyLatentImage"},
            "5": {
                "inputs": {
                    "seed": random.randint(1, 1125899906842624),
                    "steps": 30,
                    "cfg": 7,
                    "sampler_name": "dpmpp_2m_sde",
                    "scheduler": "karras",
                    "denoise": 1,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0],
                },
                "class_type": "KSampler",
            },
            "6": {"inputs": {"samples": ["5", 0], "vae": ["1", 2]}, "class_type": "VAEDecode"},
            "7": {"inputs": {"image": random_face}, "class_type": "LoadImage"},
            "8": {
                "inputs": {
                    "enabled": True,
                    "input_image": ["6", 0],
                    "source_image": ["7", 0],
                    "swap_model": "inswapper_128.onnx",
                    "facedetection": "retinaface_resnet50",
                    "face_restore_model": "codeformer-v0.1.0.pth",
                    "face_restore_visibility": 0.8,
                    "codeformer_weight": 0.7,
                    "detect_gender_input": "no",
                    "detect_gender_source": "no",
                    "input_faces_index": "0",
                    "source_faces_index": "0",
                    "console_log_level": 1,
                },
                "class_type": "ReActorFaceSwap",
            },
            "10": {"inputs": {"model_name": "bbox/face_yolov8m.pt"}, "class_type": "UltralyticsDetectorProvider"},
            "11": {
                "inputs": {
                    "guide_size": 384,
                    "guide_size_for": "bbox",
                    "max_size": 1024,
                    "seed": random.randint(1, 1125899906842624),
                    "steps": 25,
                    "cfg": 6.5,
                    "sampler_name": "dpmpp_2m_sde",
                    "scheduler": "karras",
                    "denoise": 0.35,
                    "feather": 5,
                    "noise_mask": True,
                    "force_inpaint": True,
                    "bbox_threshold": 0.5,
                    "bbox_dilation": 0,
                    "bbox_crop_factor": 3.0,
                    "sam_detection_hint": "center-1",
                    "sam_dilation": 0,
                    "sam_threshold": 0.93,
                    "sam_bbox_expansion": 0,
                    "sam_mask_hint_threshold": 0.7,
                    "sam_mask_hint_use_negative": "False",
                    "drop_size": 10,
                    "wildcard": "",
                    "cycle": 1,
                    "image": ["8", 0],
                    "model": ["1", 0],
                    "clip": ["1", 1],
                    "vae": ["1", 2],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "bbox_detector": ["10", 0],
                },
                "class_type": "FaceDetailer",
            },
            "12": {"inputs": {"model_name": "ESRGAN/4x-UltraSharp.pth"}, "class_type": "UpscaleModelLoader"},
            "13": {"inputs": {"upscale_model": ["12", 0], "image": ["11", 0]}, "class_type": "ImageUpscaleWithModel"},
            "14": {
                "inputs": {"upscale_method": "bicubic", "scale_by": 0.5, "image": ["13", 0]},
                "class_type": "ImageScaleBy",
            },
            "9": {
                "inputs": {"filename_prefix": f"Narrative/{target_model.replace(' ', '')}_HQ", "images": ["14", 0]},
                "class_type": "SaveImage",
            },
        }

        worker = threading.Thread(target=self._post_to_comfy, args=(mock_workflow,))
        worker.daemon = True
        worker.start()
        logger.info("--> [Async Worker] Image sent to ComfyUI queue. Voice engine returning instantly.")
        return final_positive_prompt
