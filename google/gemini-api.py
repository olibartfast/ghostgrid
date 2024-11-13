import argparse
import os
import google.generativeai as genai

def generate(prompt, model_name, system_prompt, max_tokens, temperature, top_p, top_k):
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    generation_config = {
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "max_output_tokens": max_tokens,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=generation_config,
        system_instruction=system_prompt,
    )

    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(prompt)

    print(response.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate content using Google's Gemini model")
    parser.add_argument("prompt", type=str, help="The prompt for content generation")
    parser.add_argument("--model_name", type=str, default="gemini-1.5-pro-002", help="Name of the Gemini model to use")
    parser.add_argument("--system_prompt", type=str, default="You are a helpful AI assistant.", help="System prompt to set the context")
    parser.add_argument("--max_tokens", type=int, default=8192, help="Maximum number of output tokens")
    parser.add_argument("--temperature", type=float, default=1.0, help="Temperature for generation")
    parser.add_argument("--top_p", type=float, default=0.95, help="Top p value for generation")
    parser.add_argument("--top_k", type=int, default=40, help="Top k value for generation")
    
    args = parser.parse_args()
    
    generate(args.prompt, args.model_name, args.system_prompt, args.max_tokens, args.temperature, args.top_p, args.top_k)