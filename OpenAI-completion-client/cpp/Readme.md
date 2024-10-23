# OpenAI Completion Client

A C++ command-line interface (CLI) tool for sending multimodal prompts (text and images) to Large Language Model (LLM) APIs compatible with OpenAI's chat completions format. The tool supports multiple API providers and can handle both local images and image URLs in prompts.

## Key Features

- **Multiple API Provider Support**: Compatible with various providers including:
  - OpenAI
  - Together
  - vLLM
  - Anthropic
  - Google
- **Multimodal Capabilities**: 
  - Submit text alongside multiple images
  - Support for both local image files and image URLs
  - Automatic image preprocessing (resizing while maintaining aspect ratio)
- **Image Processing Options**:
  - Customizable target image size
  - Multiple detail levels for image analysis (low, auto, high)
  - Automatic square padding for non-square images
- **API Configuration**:
  - Environment variable integration for API keys and endpoints
  - Custom endpoint URL support
  - Configurable maximum token limit for responses

## Dependencies

- C++17 or later
- CURL (for HTTP requests)
- nlohmann/json (JSON handling)
- cxxopts (command-line argument parsing)
- OpenCV (image processing)
- base64.h (Base64 encoding)

## Environment Variables

Set up your API credentials using environment variables and pass it as cli input.

## Usage

Basic command structure:

```bash
./openai-completion-client \
    --prompt <text_prompt> \
    --images <image_paths...> \
    --model <model_name> \
    --api_endpoint <api_provider_endpoint>
    --api_key_env <api_provider_key_env_var> \
    [optional parameters]
```

### Command Line Options

- `-p, --prompt`: Text prompt for image analysis
- `-i, --images`: One or more image file paths or URLs
- `-m, --model`: Model name to use (depending on api provider e.g., gpt-4o, claude3.5, lama3.2-90b vision...)
- `-e, --api_endpoint`: API endpoint URL (depends from provider) 
- `-a  --api_key_env ` : API key to read via environment variable, 
- `-d, --detail`: Image detail level (low, auto, high) [default: low]
- `-t, --tokens`: Maximum tokens for response [default: 300]
- `-s, --size`: Target image size for encoding [default: 512]
- `-h, --help`: Print usage information

### Example Commands

1. Analyze local images:
```bash
./openai-completion-client \
    --prompt "Compare these images" \
    --images image1.jpg image2.jpg \
    --model gpt-4o \
    --api_endpoint https://api.openai.com/v1/chat/completions \
    --detail low \
    --tokens 100
```

## Image Processing Details

- Images are automatically resized to maintain aspect ratio
- Non-square images are padded with black borders to create square output
- Final images are encoded as base64 JPEG before API submission
- URLs are passed directly to the API without modification

