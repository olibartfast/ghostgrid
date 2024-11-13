import argparse
import base64
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, Content
import os

def generate(prompt, system_prompt, model,  region, project, credentials, max_tokens, temperature, top_p):
    vertexai.init(project=project, location=region)
    model = GenerativeModel(
        model,
    )

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials
    
    generation_config = {
        "max_output_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }
    
    # Create content with system prompt and user prompt
    content = [
        Content(
            role="user",
            parts=[
                Part.from_text(system_prompt),
                Part.from_text(prompt)
            ]
        )
    ]
    
    responses = model.generate_content(
        content,
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=True,
    )

    for response in responses:
        print(response.text, end="")

safety_settings = [
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
    SafetySetting(
        category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=SafetySetting.HarmBlockThreshold.OFF
    ),
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate content using Vertex AI Gemini model")
    parser.add_argument("prompt", type=str, help="The prompt for content generation")
    parser.add_argument("--system_prompt", type=str, default="You are a helpful AI assistant.", help="System prompt to set the context")
    parser.add_argument("--max_tokens", type=int, default=8192, help="Maximum number of output tokens")
    parser.add_argument("--temperature", type=float, default=1.0, help="Temperature for generation")
    parser.add_argument("--top_p", type=float, default=0.95, help="Top p value for generation")
    parser.add_argument("--model", type=str, default="gemini-1.5-flash-002", help="Model to use")
    parser.add_argument("--credentials", type=str, help="Path to credentials file")
    parser.add_argument("--project", type=str, help="GCP project ID")
    parser.add_argument("--region", type=str, help="GCP region")

    
    args = parser.parse_args()
    
    generate(args.prompt, args.system_prompt, args.model, args.region, args.project, args.credentials, args.max_tokens, args.temperature, args.top_p)