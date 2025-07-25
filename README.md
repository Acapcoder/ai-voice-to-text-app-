# ai-voice-to-text-app
A locally hosted AI voice-to-text to text app using Llama 2-7. 

 Requirements

- Python 3.8+
- pip (Python package installer)
- 4GB+ RAM (8GB+ recommended for faster inference)
- Internet connection (for downloading the model)

---

 Step 1: Download the LLaMA Model

1. Go to [TheBloke's Hugging Face page](https://huggingface.co/TheBloke).
2. Search for a quantized LLaMA model like:

   👉 [`TheBloke/Llama-2-7B-Chat-GGUF`](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF)

3. Choose a `.gguf` file (e.g., `llama-2-7b-chat.Q4_K_M.gguf`).
4. Download it and save it in the `models/` folder in your project directory (create the folder if needed).

---

 Step 2: Install Python Dependencies

Run the following command to install all required libraries:
Bash
pip install -r requirements.txt
