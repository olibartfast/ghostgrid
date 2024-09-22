# OpenAI Image Analysis CLI Tool

This tool allows you to analyze images using OpenAI's API, providing prompts and image files via the command line. It can handle both URLs and local image files, which are encoded as base64 before being sent to the API.

## Features

- Supports multiple image inputs (local files)
- Configurable text prompts
- Model and API endpoint specification
- CLI parameters for detailed image analysis (detail levels)
- Automatically reads OpenAI API key from the environment

## Requirements

- **C++17 or later**
- **CURL**: For making HTTP requests.
- **nlohmann/json**: For JSON parsing and serialization.
- **cxxopts**: For parsing command line options.
- **Rene Nyffenegger's Base64 Library**: For base64 encoding of local images.

## Usage

### Command-line Parameters

- `--prompt, -p`: Text prompt for image analysis.
- `--images, -i`: Paths to local image files (multiple images supported).
- `--model, -m`: OpenAI model name (default: `gpt-4o-mini`).
- `--url, -u`: OpenAI API endpoint URL (default: `https://api.openai.com/v1/chat/completions`).
- `--detail, -d`: Image detail level (`auto`, `low`, `high`; default: `low`).
- `--tokens, -t`: Maximum tokens for the response (default: 300).
- `--help, -h`: Print usage information.

### Example Command

```bash
./openai_image_analysis \
    --prompt "Analyze these images for content differences" \
    --images image1.jpg image2.jpg \
    --model gpt-4o-mini \
    --url https://api.openai.com/v1/chat/completions \
    --detail high \
    --tokens 300
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


