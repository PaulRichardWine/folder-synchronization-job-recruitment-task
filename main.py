import hashlib
import os
import json
import shutil
import datetime
import time

def print_pretty_dict(dictionary):
    """Print a dictionary in a pretty format."""
    print(json.dumps(dictionary, indent=4, sort_keys=True))

def calculate_md5(filename, chunk_size=8192):
    md5 = hashlib.md5()
    with open(filename, 'rb') as file:
        while True:
            data = file.read(chunk_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def is_file(address):
    return (os.path.isfile(address))

def is_folder(address):
    return (os.path.isdir(address))


def make_dir_dict(dir_path):
    content = {}
    for item_name in os.listdir(dir_path):
        full_element_path = os.path.join(dir_path, item_name)
        if is_file(full_element_path):
            content[item_name] = calculate_md5(full_element_path)
        if is_folder(full_element_path):
            content[item_name] = make_dir_dict(full_element_path)
    return content


def timestamp():
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    return timestamp

def log_to_file(text, filepath):
    with open(filepath, 'a', encoding='utf-8') as file:
        file.write(text + '\n')

def print_and_log(func, log_path = input("Enter the log file path: ")):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        output = ( timestamp(), func.__name__ , result )
        output_str = ", ".join(map(str, output))
        print(output_str)
        log_to_file(output_str, log_path)
        return result
    return wrapper


def try_except_wrapper(func):
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            traceback.print_exc()
            return f"An error occurred in function '{func.__name__}' at timestamp '{timestamp()}': {str(e)}"
    return wrapper

@try_except_wrapper
@print_and_log
def delete_file(path):
    os.remove (path)
    return path


def list_folder_files (path):
    files_list = []
    for root, dirs, files in os.walk(path):
        for file in files:
            files_list.append(os.path.join(root, file))
    return files_list

@try_except_wrapper
@print_and_log
def delete_folder(path):
    deleted_files = list_folder_files(path)
    shutil.rmtree(path)
    return path, deleted_files


def delete_unnecessary(source_dict, source_path, destination_dict, destination_path):
    # Delete files and folders in destination folder that are not present in source folder
    for item_name, item_value in destination_dict.items():
        destination_item_full_path = os.path.join(destination_path, item_name)

        if item_name not in source_dict:
            # Destination item doesn't exist in source folder, delete it
            if is_file(destination_item_full_path):
                delete_file(destination_item_full_path)
            elif is_folder(destination_item_full_path):
                delete_folder(destination_item_full_path)
        elif is_file(destination_item_full_path):
            # Compare file MD5 hashes before deletion
            source_md5 = source_dict[item_name]
            destination_md5 = item_value
            if source_md5 != destination_md5:
                delete_file(destination_item_full_path)

        elif is_folder(destination_item_full_path):
            # Recursively check subfolders for deletion
            delete_unnecessary(source_dict.get(item_name, {}), source_path, item_value, destination_item_full_path)

@try_except_wrapper
@print_and_log
def copy_file (source_path, destination_path):
    shutil.copy2(source_path, destination_path)
    return {"copied file:": source_path, "created file:": destination_path }

@try_except_wrapper
@print_and_log
def copy_folder(source_path, destination_path):
    shutil.copytree(source_path, destination_path)
    copied_files = list_folder_files(source_path)
    created_files = list_folder_files(destination_path)
    return {"copied_files": copied_files, "created_files": created_files}


def copy_missing_files(source_dict, source_path, destination_dict, destination_path):
    for item_name, item_data in source_dict.items():
        source_item_full_path = os.path.join(source_path, item_name)
        destination_item_full_path = os.path.join(destination_path, item_name)

        if is_file(source_item_full_path):
            if item_name not in destination_dict:
                # If the file doesn't exist in the destination directory, copy it
                copy_file(source_item_full_path, destination_item_full_path)
        elif is_folder(source_item_full_path):
            if item_name not in destination_dict:
                # If the folder doesn't exist in the destination directory, copy the entire folder
                copy_folder(source_item_full_path, destination_item_full_path)
            else:
                # If the folder exists in the destination directory, recursively traverse into the subfolder
                copy_missing_files(item_data, source_item_full_path, destination_dict[item_name], destination_item_full_path)



source_path = input ("Enter source folder path: ")
destination_path = input ("Enter destination folder path: ")
synchronization_interval = input ("Enter synchronization interval in seconds: ")



while True:
    source_dict = (make_dir_dict(source_path))
    destination_dict = (make_dir_dict(destination_path))

    delete_unnecessary(source_dict, source_path, destination_dict, destination_path)
    copy_missing_files(source_dict, source_path, destination_dict, destination_path)

    time.sleep(int(synchronization_interval))





