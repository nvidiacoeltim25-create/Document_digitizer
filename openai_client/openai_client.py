import base64
from openai import OpenAI
from llm_confidence.logprobs_handler import LogprobsHandler
from utils.constants import OPENAI_API_KEY, OPENAI_MODEL


def infer_openai_1(filepath, prompt):
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Initialize the LogprobsHandler
    logprobs_handler = LogprobsHandler()

    with open(filepath, "rb") as image_file:
        b64_imagee = base64.b64encode(image_file.read()).decode("utf-8")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        # max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_imagee}"}},
                ],
            }
        ],
        logprobs=True,
        # response_format={'type': 'json_object'}
    )
    # print(response.choices[0])
        # Extract the log probabilities from the response
    response_logprobs = response.choices[0].logprobs.content if hasattr(response.choices[0], 'logprobs') else []

    # Format the logprobs from OpenAI
    logprobs_formatted = logprobs_handler.format_logprobs(response_logprobs)

    # Process the log probabilities to get confidence scores
    confidence = logprobs_handler.process_logprobs(logprobs_formatted)

    # Print the confidence scores
    print("CONFIDENCE:", confidence)
    # print(f"FILE PATH: {filepath}: \n", response.choices[0].message.content)
    return response.choices[0].message.content