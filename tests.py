from functions.get_files_info import get_files_info, get_file_content, write_file, run_python_file

def print_files_info(title, files_info):
    if isinstance(files_info, str):
        print(f"{files_info}")
        return
    for entry in files_info:
        name = entry.get("name")
        file_size = entry.get("file_size")
        is_dir = entry.get("is_dir")
        print(f" - {name}: file_size={file_size} bytes, is_dir={is_dir}")

if __name__ == "__main__":

    # result = get_files_info("calculator", ".")
    # print_files_info("current directory", result)


    # result = get_file_content("calculator", "main.py")
    # print(result)


    # result = write_file("calculator", "lorem.txt", "wait, this isn't lorem ipsum")
    # print(result)



    result = run_python_file("calculator", "main.py") #(should print the calculator's usage instructions)
    print(result)
    result = run_python_file("calculator", "main.py", ["3 + 5"]) #(should run the calculator... which gives a kinda nasty rendered result)
    print(result)
    result = run_python_file("calculator", "tests.py")
    print(result)
    result = run_python_file("calculator", "../main.py") #(this should return an error)
    print(result)
    result = run_python_file("calculator", "nonexistent.py") #(this should return an error)
    print(result)
