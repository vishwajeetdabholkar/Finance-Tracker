import os

# List of files and extensions to ignore
IGNORE_FILES = ['README.md', 'requirements.txt', '__init__.py', '.gitignore']
IGNORE_EXTENSIONS = ['.pyc', '.db', '.png', '.jpg', '.jpeg', '.gif', '.svg']

def should_include_file(filename):
    if filename in IGNORE_FILES:
        return False
    if any(filename.endswith(ext) for ext in IGNORE_EXTENSIONS):
        return False
    return True

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Skip empty files
            if not content.strip():
                return None
            return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

def compile_project(root_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as out_file:
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if not should_include_file(file):
                    continue
                
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, root_dir)
                
                # Skip the output file itself
                if relative_path == output_file:
                    continue
                
                content = read_file(file_path)
                if content is None:
                    continue  # Skip empty files
                
                out_file.write(f"File: {relative_path}\n\n")
                out_file.write(content)
                out_file.write("\n\n=======\n\n")

if __name__ == "__main__":
    root_directory = "."  # Current directory
    output_file = "project.txt"
    compile_project(root_directory, output_file)
    print(f"Project compilation complete. Output saved to {output_file}")