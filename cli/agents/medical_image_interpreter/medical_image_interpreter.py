# from __future__ import annotations
# import asyncio
# from typing import Annotated
# from genai_session.session import GenAISession
# from genai_session.utils.context import GenAIContext
# from io import BytesIO
# from typing import Annotated, Any
# import torch, transformers
# from PIL import Image
# from torchvision import transforms


# ########## Model Initialization ##########
# CKPT = "aehrc/medicap"


# class MedicapSingleton:
#     """Singleton that captions medical images (model loads on first instantiation)."""

#     _instance: "MedicapSingleton | None" = None

#     def __new__(cls) -> "MedicapSingleton":      # ← singleton gatekeeper
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#             cls._instance._eager_load()          # load once
#         return cls._instance

#     # ---------------------------------------------------------
#     def _eager_load(self) -> None:
#         """Load model, tokenizer, and transforms exactly once."""
#         # Pick device: CUDA ▸ MPS ▸ CPU
#         self.device = (
#             torch.device("cuda")
#             if torch.cuda.is_available() else
#             torch.device("mps") if torch.backends.mps.is_available() else
#             torch.device("cpu")
#         )

#         self.model = (
#             transformers.AutoModel.from_pretrained(CKPT, trust_remote_code=True)
#             .to(self.device)
#             .eval()
#         )
#         self.tok = transformers.AutoTokenizer.from_pretrained(CKPT)

#         proc = transformers.AutoImageProcessor.from_pretrained(CKPT)
#         self.tfm = transforms.Compose(
#             [
#                 transforms.Resize(proc.size["shortest_edge"]),
#                 transforms.CenterCrop([proc.size["shortest_edge"]]*2),
#                 transforms.ToTensor(),
#                 transforms.Normalize(proc.image_mean, proc.image_std),
#             ]
#         )

#     # ---------------------------------------------------------
#     def caption(self, img_bytes: bytes) -> str:
#         """Return a medical caption for raw image bytes."""
#         img = Image.open(BytesIO(img_bytes)).convert("RGB")
#         tensor = self.tfm(img).unsqueeze(0).to(self.device)
#         with torch.no_grad():
#             seq = self.model.generate(
#                 pixel_values=tensor,
#                 bos_token_id=self.tok.bos_token_id,
#                 eos_token_id=self.tok.eos_token_id,
#                 pad_token_id=self.tok.pad_token_id,
#                 max_length=256,
#                 num_beams=4,
#             )
#         return self.tok.decode(seq[0], skip_special_tokens=True)


# # Global singleton instance created immediately at import time
# print("Loading model...")
# _MEDICAP = MedicapSingleton()
# print("Model loaded")

# ########Agent Configuration########
# AGENT_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZTBmOTg3My05ZDliLTQwMzYtYWYwZC03MWJjNmMyODUzYTIiLCJleHAiOjI1MzQwMjMwMDc5OSwidXNlcl9pZCI6IjY5NjVlNWMwLTE0MzQtNDkzNS1hYTAwLWFjZTIxNTVmMTE5YSJ9.DMklvMaav3FBzsbOk-WZyIuPzK1AiFtQ5-zd1Kp90VU" # noqa: E501
# session = GenAISession(jwt_token=AGENT_JWT)


# @session.bind(
#     name="medical_image_interpreter",
#     description="This agent interpret the result from medical image"
# )
# async def medical_image_interpreter(
#         agent_context,
#         file_id: Annotated[str, "ID of the file to read"]
# ):
#     file = await agent_context.files.get_by_id(file_id)
#     caption = _MEDICAP.caption(file.read())
#     if caption is None:
#         return "No caption found"
#     return caption


# async def main():
#     print(f"Agent with token '{AGENT_JWT}' started")
#     await session.process_events()

# if __name__ == "__main__":
#     asyncio.run(main())
