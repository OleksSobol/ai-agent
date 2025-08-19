import os
import subprocess
from google.genai import types

from config import MAX_CHARS

def get_files_info(working_directory, directory="."):
    try:
        full_path = os.path.join(working_directory, directory) # validate it stays within the working directory boundaries.
        abs_working_directory = os.path.abspath(working_directory)
        abs_full_path = os.path.abspath(full_path)

        if not abs_full_path.startswith(abs_working_directory):
            return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

        if not os.path.isdir(abs_full_path):
            return f'Error: "{directory}" is not a directory'

        entries = []
        for entry in os.listdir(abs_full_path):
            entry_path = os.path.join(abs_full_path, entry)
            is_dir = os.path.isdir(entry_path)
            try:
                file_size = os.path.getsize(entry_path)
            except Exception as e:
                return f'Error: Could not get size for "{entry}": {e}'
            entries.append(f'- {entry}: file_size={file_size} bytes, is_dir={is_dir}')

        return "\n".join(entries)
    except Exception as e:
        return f'Error: {e}'


def get_file_content(working_directory, file_path):
    try:
        abs_working_directory = os.path.abspath(working_directory)
        abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))

        if not abs_file_path.startswith(abs_working_directory):
            return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

        if not os.path.isfile(abs_file_path):
            return f'Error: File not found or is not a regular file: "{file_path}"'

        with open(abs_file_path, "r", encoding="utf-8") as f:
            join_str = f' [...File "{abs_file_path}" truncated at {MAX_CHARS} characters]'
            stream = f.read(MAX_CHARS)
            if len(stream) > MAX_CHARS:
                return stream + join_str
            return stream
    except Exception as e:
        return f'Error: {e}'
    
        
def write_file(working_directory, file_path, content):

    try:
        abs_working_directory = os.path.abspath(working_directory)
        abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))

        # If the file_path is outside of the working_directory, return a string with an error:
        if not abs_file_path.startswith(abs_working_directory):
            return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'
        
        # If the file_path doesn't exist, create it. As always, if there are errors, return a string representing the error, prefixed with "Error:".
        os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)
        
        with open(abs_file_path, "w", encoding="utf-8") as file:
            file.write(content)

        return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'

    except Exception as e:
        return f"Error: {e}"
        
def run_python_file(working_directory, file_path, args=[]):
    try:
        abs_working_directory = os.path.abspath(working_directory)
        abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
        
        #If the file_path is outside the working directory, return a string with an error:
        if not abs_file_path.startswith(abs_working_directory):
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
        
        #If the file_path doesn't exist, return an error string:
        if not os.path.isfile(abs_file_path):
            return f'Error: File "{file_path}" not found.'

        #If the file doesn't end with ".py", return an error string:
        if not abs_file_path.endswith(".py"):
            return f'Error: "{file_path}" is not a Python file.'
        
        cmd = ["python3", abs_file_path] + args
        completed_process = subprocess.run(
            cmd,
            timeout=30,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=abs_working_directory,
            text=True
        )
        stdout = completed_process.stdout.strip()
        stderr = completed_process.stderr.strip()
        output = []

        if stdout:
            output.append(f"STDOUT:\n{stdout}")
        if stderr:
            output.append(f"STDERR:\n{stderr}")
        if completed_process.returncode != 0:
            output.append(f"Process exited with code {completed_process.returncode}")

        if not output:
            return "No output produced."
        return "\n".join(output)
        
    except Exception as e:
        return f"Error: executing Python file: {e}"


schema_get_files_info = types.FunctionDeclaration(
    name="get_files_info",
    description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "directory": types.Schema(
                type=types.Type.STRING,
                description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
            ),
        },
    ),
)


#  Following the same pattern that we used for schema_get_files_info, create function declarations for:
schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Reads the content of a specified file within the working directory, truncating if it exceeds the maximum allowed characters.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file to read, relative to the working directory.",
            ),
        },
    ),
)

schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Executes a Python file within the working directory with optional arguments and returns its output.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the Python file to execute, relative to the working directory.",
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="Optional list of arguments to pass to the Python script.",
            ),
        },
    ),
)

schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes content to a specified file within the working directory, creating directories as needed.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The path to the file to write, relative to the working directory.",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The content to write to the file.",
            ),
        },
    ),
)


available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_run_python_file,
        schema_write_file,
    ]
)

def call_function(function_call_part, verbose=False):
    if verbose:
        print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    else:
        print(f" - Calling function: {function_call_part.name}")

    func_map = {
        "get_files_info": get_files_info,
        "get_file_content": get_file_content,
        "run_python_file": run_python_file,
        "write_file": write_file,
    }

    function_name = function_call_part.name
    func = func_map.get(function_name)
    if not func:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )

    # Prepare arguments, always set working_directory to "./calculator"
    args = function_call_part.args.copy()
    args["working_directory"] = "./calculator"

    try:
        function_result = func(**args)
    except Exception as e:
        function_result = f"Error: Exception during function call: {e}"

    return types.Content(
    role="tool",
    parts=[
        types.Part.from_function_response(
            name=function_name,
            response={"result": function_result},
        )
    ],
)
