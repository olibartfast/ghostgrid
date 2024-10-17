# OpenAI API-Compliant C++ Multimodal Inference Client

This project provides a command-line interface (CLI) tool that allows users to send multimodal prompts (text and images) to OpenAI's API. The tool can process text inputs alongside image files, either from local storage or URLs, encoding local images as base64 before transmitting them. It supports any language model (LLM) framework compatible with OpenAI's API, such as **vLLM**.

## Features

- **Multimodal Support**: Submit text and multiple images (from URLs or local files).
- **Customizable Prompts**: Input custom text prompts for image analysis.
- **API Flexibility**: Compatible with multiple API providers (OpenAI, Together, vLLM).
- **Detailed Image Analysis**: Set desired detail levels (`low`, `auto`, `high`).
- **Environment Variable Integration**: Automatically reads API keys and endpoints from environment variables.
  
## Requirements

- **C++17 or later**
- **CURL**: For handling HTTP requests.
- **nlohmann/json**: For JSON serialization and deserialization.
- **cxxopts**: For parsing command-line options.
- **OpenCV**: For image processing and resizing.
- **Rene Nyffenegger's Base64 Library**: For encoding image data as base64.

## Usage

### Command-Line Parameters

- `--prompt, -p`: The text prompt for image analysis.
- `--images, -i`: Paths to local image files (multiple files supported).
- `--model, -m`: OpenAI model name (default: `gpt-4o-mini`).
- `--url, -u`: OpenAI API endpoint URL (default: `https://api.openai.com/v1/chat/completions`).
- `--detail, -d`: Image detail level (`auto`, `low`, `high`; default: `low`).
- `--tokens, -t`: Maximum tokens for the API response (default: 300).
- `--provider, -r`: API provider name (e.g., `openai`, `together`, `vllm`).
- `--size, -s`: Image size for encoding (default: 512 pixels).
- `--help, -h`: Display help information.

### Example Command

```bash
./openai-completion-client \
    --prompt "Analyze these images for content differences" \
    --images image1.jpg image2.jpg \
    --model gpt-4o-mini \
    --url https://api.openai.com/v1/chat/completions \
    --detail high \
    --tokens 300
```

### Environment Variables

- **OPENAI_API_KEY**: The API key for OpenAI.
- **TOGETHER_API_KEY**: The API key for Together AI.
- **OPENAI_ENDPOINT**: Custom endpoint URL (optional for OpenAI users).
- **TOGETHER_ENDPOINT**: Endpoint URL for Together AI users.

Example setup:

```bash
export OPENAI_API_KEY="your_openai_api_key"
```

