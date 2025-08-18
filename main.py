import os
import sys
import argparse

from dotenv import load_dotenv
from google import genai
from google.genai import types

from functions.get_files_info import available_functions

MODEL_NAME = "gemini-2.0-flash-001"
ENV_API_KEY = "GEMINI_API_KEY"


def parse_arguments():
    parser = argparse.ArgumentParser(description="AI Code Assistant")
    parser.add_argument("prompt", nargs="+", help="The prompt to send to the AI")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    return parser.parse_args()

def get_api_client():
    api_key = os.environ.get(ENV_API_KEY)
    if not api_key:
        raise ValueError(f"{ENV_API_KEY} environment variable is required")
    return genai.Client(api_key=api_key)

def create_messages(user_prompt):
    return [types.Content(role="user", parts=[types.Part(text=user_prompt)])]

def print_verbose_info(user_prompt, response, verbose):
    if verbose:
        print("User prompt:", user_prompt)
        print("Prompt tokens:", response.usage_metadata.prompt_token_count)
        print("Response tokens:", response.usage_metadata.candidates_token_count)



def main():
    try:
        load_dotenv()
        args = parse_arguments()

        system_prompt = """
            You are a helpful AI coding agent.

            When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

            - List files and directories

            All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
        """

       

        user_prompt = " ".join(args.prompt)
        client = get_api_client()
        messages = create_messages(user_prompt)

        print("Hello from AI agent!")

         # Call the model to get the response
        response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=messages,
            config=types.GenerateContentConfig(
                tools=[available_functions], 
                system_instruction=system_prompt
                )
        )
        if hasattr(response, "function_calls") and response.function_calls:
            for function_call_part in response.function_calls:
                print(f"Calling function: {function_call_part.name}({function_call_part.args})")
        else:
            print(response.text)

        print_verbose_info(user_prompt, response, args.verbose)

        print(response.text)


    except ValueError as e:
        print(f"Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    result_code = main()
    sys.exit(result_code)