# Image Analysis using OpenAI API

This project provides a Python-based script to analyze images using OpenAI's API. It supports image files or URLs as input and generates a response based on a text prompt using the GPT model. The script encodes local images in Base64 format or accepts image URLs directly.

## Features

- Supports local image files or URLs.
- Sends text prompts alongside images for analysis.
- Leverages OpenAI's API to generate detailed responses.
- Configurable prompt, model, token count, and detail level.

## Prerequisites

- Python 3.x
- OpenAI API key (set as an environment variable)
- `requests` library

You can install dependencies using:

```bash
pip install requests
```

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/olibartfast/vision-language-models-playground.git
cd vision-language-models-playground/OpenAI-client/python
```


### 3. Run the Script

You can run the script using the following command:

```bash
python image_analysis.py --prompt "your prompt" --images image1.jpg ... imageN.jp  --model openai_model_name --tokens max_token_output
```

**Arguments:**

- `--prompt` (optional): Text prompt for image analysis (default: `"What's in this image?"`).
- `--images` (required): List of image file paths or URLs.
- `--model` (optional): GPT model to use (default: `gpt-4o-mini`).
- `--url` (optional): API endpoint URL (default: `https://api.openai.com/v1/chat/completions`).
- `--detail` (optional): Detail level for image analysis (default: `low`).
- `--tokens` (optional): Maximum number of tokens in the response (default: `300`).

### Example Usage

Analyze an image using the script:

```bash
python image_analysis.py -p "Describe this image" -i image.jpg -m gpt-4o-mini -t 300
```

### Environment Variables

- **OPENAI_API_KEY**: The API key for OpenAI must be set as an environment variable.

Example:
```bash
export OPENAI_API_KEY="your_openai_api_key"
```

### Notes

- The program automatically encodes local images as base64 before sending them in the request.
- Output will display the API's JSON response.


### Reference
* https://platform.openai.com/docs/guides/vision