import os
import subprocess
import sys

def run_python_file(
    working_directory: str, file_path: str, args: list[str] | None = None
) -> str:
    try:
        working_dir_abs = os.path.abspath(working_directory)
        target_file = os.path.normpath(os.path.join(working_dir_abs, file_path))

        valid_target_file = (
            os.path.commonpath([working_dir_abs, target_file]) == working_dir_abs
        )

        if not valid_target_file:
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'
        
        if not os.path.isfile(target_file):
            return f'Error: "{file_path}" does not exist or is not a regular file'

        if not target_file.endswith(".py"):
            return f'Error: "{file_path}" is not a Python file'
        
        command = [sys.executable, target_file]

        if args:
            command.extend(args)

        completed = subprocess.run (
            command,
            cwd=working_dir_abs,
            capture_output = True,
            text = True,
            timeout= 30,
        )

        output_parts = []
        if completed.returncode != 0:
            output_parts.append(f"Process exited with code {completed.returncode}")
        
        if not completed.stderr and not completed.stdout:
            output_parts.append("No output produced")
        else:
            if completed.stdout:
                output_parts.append(f"STDOUT:\n{completed.stdout.rstrip()}")
            if completed.stderr:
                output_parts.append(f"STDERR:\n{completed.stderr.rstrip()}")
            
        return "\n".join(output_parts)

    except Exception as e:
        return f'Error: {e}'


schema_run_python_file = {
    "type": "function",
    "function": {
        "name": "run_python_file",
        "description": "Executes a Python file relative to the working directory with optional command-line arguments and returns its output",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the Python (.py) file to execute, relative to the working directory",
                },
                "args": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                    "description": "Optional list of string arguments to pass to the Python script",
                },
            },
            "required": ["file_path"],
        },
    },
}