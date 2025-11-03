import base64
from huggingface_hub import InferenceClient
from utils.constants import HUGGINGFACE_KEY, HUGGINGFACE_MODEL

def huggingface_infer(filepath: str, prompt: str, model: str = "meta-llama/Llama-3.2-11B-Vision-Instruct") -> str:
    """
    Describe an image using a Hugging Face Vision model.

    Parameters:
        filepath (str): Path to the local image file.
        prompt (str): Instruction or question about the image.
        api_key (str): Hugging Face API key.
        model (str): Model name (default is LLaMA 3.2 Vision Instruct).

    Returns:
        str: The model's response.
    """
    # Load and encode the image
    with open(filepath, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Create a data URI
    data_uri = f"data:image/jpeg;base64,{encoded_image}"

    # Initialize the client
    client = InferenceClient(provider="hf-inference", api_key=HUGGINGFACE_KEY)

    # Send the request
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ]
            }
        ],
    )

    return completion.choices[0].message.content


response = describe_image(
    filepath="/home/ujjwal-ltim/ujjwal/computershare/email_st/attachments_db/0f5eaede-5f5d-49ab-9f48-930cb63a35eb.jpg",
    prompt="What is happening in this image?",
)

print(response)
