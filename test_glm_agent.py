#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the backend directory to path
sys.path.append('/mnt/c/Users/pietr/Documents/progetto/tutor-ai/backend')

from services.llm_service import LLMService

async def test_glm_slide_agent():
    """Test the GLM Slide Agent directly"""

    print("Testing GLM Slide Agent...")

    # Initialize LLM Service
    llm_service = LLMService()

    print(f"LLM Service type: {llm_service.model_type}")
    print(f"Has GLM Slide Agent method: {hasattr(llm_service, 'generate_slides_with_glm_slide_agent')}")
    print(f"ZAI Manager available: {llm_service.zai_manager is not None}")

    if hasattr(llm_service, 'generate_slides_with_glm_slide_agent') and llm_service.model_type == "zai":
        print("✅ Conditions met for GLM Slide Agent")

        result = await llm_service.generate_slides_with_glm_slide_agent(
            course_id="e9195d61-9bd2-4e30-a183-cee2ab80f1b9",
            topic="Geografia Storica",
            content_context="Test di generazione slide con GLM Slide Agent",
            num_slides=5,
            style="modern"
        )

        print(f"Result: {result}")

        if result.get("success"):
            print("✅ GLM Slide Agent succeeded!")
            print(f"Slide file: {result.get('slide_file_path')}")
        else:
            print(f"❌ GLM Slide Agent failed: {result.get('error')}")
    else:
        print("❌ Conditions not met for GLM Slide Agent")

if __name__ == "__main__":
    asyncio.run(test_glm_slide_agent())