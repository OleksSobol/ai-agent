import os
import sys
import argparse

from dotenv import load_dotenv
from google import genai
from google.genai import types

from functions.get_files_info import available_functions, call_function
from config import MAX_ITERS
from prompts import system_prompt

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

def print_func_output(function_call_result, args):
    if not function_call_result.parts[0].function_response.response:
        raise Exception(f"Error calling function: {function_call_result.parts[0].function_response.response}")
    if function_call_result and args.verbose:
        print(f"-> {function_call_result.parts[0].function_response.response}")
    return function_call_result.parts[0]


def generate_content(client, messages, user_prompt, args):
    response = client.models.generate_content(
            model=MODEL_NAME, 
            contents=messages,
            config=types.GenerateContentConfig(
                tools=[available_functions], 
                system_instruction=system_prompt
            )
        )
   

    if response.candidates:
        for candi in response.candidates:
            function_call_content = candi.content
            messages.append(function_call_content)
    
    if not response.function_calls:
        return response.text

    function_responses = []
    
    if hasattr(response, "function_calls") and response.function_calls:
        for function_call_part in response.function_calls:
            function_call_result = call_function(function_call_part, verbose=args.verbose)
            function_responses.append(print_func_output(function_call_result, args))

    else:
        print(response.text)
    
    function_responses = [resp for resp in function_responses if resp is not None]
    
    messages.append(types.Content(role="user", parts=function_responses))

    print_verbose_info(user_prompt, response, args.verbose)
    print(response.text)


def main():
    try:
        load_dotenv()
        args = parse_arguments()
        user_prompt = " ".join(args.prompt)
        client = get_api_client()
        messages = create_messages(user_prompt)

        print("AI code agent!")
        # generate_content(client, messages, user_prompt, args)
        

        iters = 0
        while True:
            iters += 1
            if iters > MAX_ITERS:
                print(f"Maximum iterations ({MAX_ITERS}) reached.")
                return 1
            try:
                final_response = generate_content(client, messages, user_prompt, args)
                if final_response:
                    print("Final response:")
                    print(final_response)
                    break
            except Exception as e:
                print(f"Error in generate_content: {e}")


    except ValueError as e:
        print(f"Configuration error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    result_code = main()
    sys.exit(result_code)