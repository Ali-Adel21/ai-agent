import argparse
import os
import sys
import time
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from config import MAX_ITERATIONS
from call_function import available_functions, call_function
from prompts import system_prompt




def main():
    load_dotenv()
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key is None:
        raise RuntimeError("api key is not found")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    parser = argparse.ArgumentParser(description="Chatbot")
    parser.add_argument("user_prompt", type=str, help="User prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": args.user_prompt},
    ]

    if args.verbose:
        print(f"User prompt: {args.user_prompt}")

    for _ in range(MAX_ITERATIONS):
        response = None
        for attempt in range(5):
            try:
                response = client.chat.completions.create(
                    model="openrouter/free",
                    messages=messages,
                    tools=available_functions,
                    temperature=0,
                )
                break
            except RateLimitError:
                if attempt == 4:
                    raise
                sleep_time = 2 * (attempt + 1)
                if args.verbose:
                    print(f"Rate limited (429), retrying in {sleep_time}s...")
                time.sleep(sleep_time)

        if response is None:
            raise RuntimeError("Failed to get a response from the model")

        if response.usage is None:
            raise RuntimeError("response usage info is missing")

        if args.verbose:
            print(f"Prompt tokens: {response.usage.prompt_tokens}")
            print(f"Response tokens: {response.usage.completion_tokens}")

        message = response.choices[0].message
        messages.append(message)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.type != "function":
                    continue
                result_message = call_function(tool_call, verbose=args.verbose)
                if not result_message.get("content"):
                    raise RuntimeError(
                        f"Empty function response for {tool_call.function.name}"
                    )
                if args.verbose:
                    print(f"-> {result_message['content']}")
                messages.append(result_message)
        else:
            if message.content:
                print(message.content)
            return

    print(
        f"Error: Reached maximum iterations ({MAX_ITERATIONS}) without a final response.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()