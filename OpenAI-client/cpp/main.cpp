#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <cstdlib>
#include <curl/curl.h>
#include <nlohmann/json.hpp>
#include "base64.h"
#include <cxxopts.hpp>

using json = nlohmann::json;

// Function to get the OpenAI API Key from environment variable
std::string get_api_key() {
    const char* api_key = std::getenv("OPENAI_API_KEY");
    if (api_key == nullptr) {
        throw std::runtime_error("OPENAI_API_KEY environment variable not set");
    }
    return std::string(api_key);
}

// Function to check if the string is a URL
bool is_url(const std::string& image_path) {
    return image_path.rfind("http://", 0) == 0 || image_path.rfind("https://", 0) == 0;
}


// Function to encode the image
std::string encode_image(const std::string& image_path) {
    std::ifstream image_file(image_path, std::ios::binary);
    if (!image_file) {
        throw std::runtime_error("Unable to open image file: " + image_path);
    }
    std::vector<unsigned char> image_data((std::istreambuf_iterator<char>(image_file)), std::istreambuf_iterator<char>());
    
    return base64_encode(image_data.data(), image_data.size());
}

// Callback function for CURL
size_t WriteCallback(void *contents, size_t size, size_t nmemb, std::string *s) {
    size_t newLength = size * nmemb;
    try {
        s->append((char*)contents, newLength);
    } catch(std::bad_alloc &e) {
        return 0;
    }
    return newLength;
}

int main(int argc, char* argv[]) {
    try {
        // Set up command line options
        cxxopts::Options options("OpenAI Image Analysis", "Analyze images using OpenAI's API");
        options.add_options()
            ("p,prompt", "Text prompt for image analysis", cxxopts::value<std::string>()->default_value("What's in this image?"))
            ("i,images", "Image file paths", cxxopts::value<std::vector<std::string>>())
            ("m,model", "Model name", cxxopts::value<std::string>()->default_value("gpt-4o-mini"))
            ("u,url", "API endpoint URL", cxxopts::value<std::string>()->default_value("https://api.openai.com/v1/chat/completions"))
            ("d,detail", "Image detail level (auto, low, high)", cxxopts::value<std::string>()->default_value("low"))
            ("t,tokens", "Max tokens for response", cxxopts::value<int>()->default_value("300"))
            ("h,help", "Print usage")
        ;
        options.parse_positional({"images"});

        auto result = options.parse(argc, argv);

        if (result.count("help") || !result.count("images")) {
            std::cout << options.help() << std::endl;
            return 0;
        }

        std::string prompt = result["prompt"].as<std::string>();
        std::vector<std::string> image_paths = result["images"].as<std::vector<std::string>>();
        std::string model = result["model"].as<std::string>();
        std::string url = result["url"].as<std::string>();
        std::string detail = result["detail"].as<std::string>();
        int max_tokens = result["tokens"].as<int>();

        // Get the API key from environment variable
        std::string api_key = get_api_key();

        // Prepare JSON payload
        json payload = {
            {"model", model},
            {"messages", json::array({
                {
                    {"role", "user"},
                    {"content", json::array()}
                }
            })},
            {"max_tokens", max_tokens}
        };

        // Add text prompt
        payload["messages"][0]["content"].push_back({
            {"type", "text"},
            {"text", prompt}
        });

        // Add images (distinguish between URLs and local files)
        for (const auto& image_path : image_paths) {
            json image_content;
            if (is_url(image_path)) {
                // If it's a URL, use it directly
                image_content = {
                    {"type", "image_url"},
                    {"image_url", {
                        {"url", image_path},
                        {"detail", detail}
                    }}
                };
            } else {
                // If it's a local file, encode it as base64
                std::string base64_image = encode_image(image_path);
                image_content = {
                    {"type", "image_url"},
                    {"image_url", {
                        {"url", "data:image/jpeg;base64," + base64_image},
                        {"detail", detail}
                    }}
                };
            }
            payload["messages"][0]["content"].push_back(image_content);
        }

        // Initialize CURL
        CURL *curl = curl_easy_init();
        if(curl) {
            struct curl_slist *headers = NULL;
            headers = curl_slist_append(headers, "Content-Type: application/json");
            headers = curl_slist_append(headers, ("Authorization: Bearer " + api_key).c_str());

            std::string response_string;
            std::string payload_string = payload.dump();

            curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
            curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
            curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload_string.c_str());
            curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
            curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response_string);

            CURLcode res = curl_easy_perform(curl);

            if(res != CURLE_OK) {
                std::cerr << "curl_easy_perform() failed: " << curl_easy_strerror(res) << std::endl;
            } else {
                std::cout << response_string << std::endl;
            }

            curl_easy_cleanup(curl);
            curl_slist_free_all(headers);
        }
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}