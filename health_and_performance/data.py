import os
from pathlib import Path
import re
import time
import pandas as pd

# get log folder path and access its files
current_dir = Path.cwd()
folder_path = os.path.join(current_dir, "log_files")

# Get the file paths of all incoming logs
def get_new_logs(folder_path):
    files = os.listdir(folder_path)
    log_files = [os.path.join(folder_path, file) for file in files if file.endswith('.csv')] 
    return log_files


def get_health_data(log_files):
    log_files_data = []
    for log_file in log_files:
        # read each log file into a pandas df for info extraction
        df = pd.read_csv(log_file, header=None)
        # Create columns in df for easy id
        column_names = ["type", "timestamp", "module_id", "sub_module_name", "line_number", "message"]
        df.columns = column_names
        log_files_data.append(df)
    return log_files_data


def init_default_dict(log_files_data):
    dictionary = {
        "server": {
            "ip=10.0.0.1": {
                "status": "INFO"
            },
            "ip=10.0.0.2": {
                "status": "INFO"
            },
        }
    }
    for log_file in log_files_data:
        for index, row in log_file.iterrows():
            if row.module_id not in dictionary:
                dictionary[row.module_id] = {"status": "INFO"}
                if row.sub_module_name not in dictionary[row.module_id]:
                    dictionary[row.module_id][row.sub_module_name] = []
            else:
                dictionary[row.module_id][row.sub_module_name]=[]
    return dictionary


def update_default_dict(log_files_data, default_dictionary):

    for log_df in log_files_data:
        for index, row in log_df.iterrows():
            
            if row.type not in ["INFO", "DEBUG"]:
                default_dictionary[row.module_id]["status"] = row.type

            if row.sub_module_name == "check_hdd":
                server, hdd, used_space, available_space = row.message.split("|")
                if row.type not in ["INFO", "DEBUG"]:
                    default_dictionary["server"][server]["status"] = row.type
                hdd_health = {
                    f"{server}|{hdd}":{
                    "status": f"{row.type}",
                    "storage": f"{used_space}|{available_space}"
                    }
                }
                default_dictionary[row.module_id][row.sub_module_name].append(hdd_health)

            elif row.sub_module_name in ["check_db", "check_rabbit", "check_uvicorn", "check_http", "check_streamlit"]:
                if row.type not in ["INFO", "DEBUG"]:
                    default_dictionary["server"][row.message]["status"] = row.type
                db_health = {
                    row.message: {
                        "status": row.type
                    } 
                }
                default_dictionary[row.module_id][row.sub_module_name].append(db_health)

            else:
                default_dictionary[row.module_id][row.sub_module_name] = {"status": row.type}
    return default_dictionary

def check_for_new_logs(folder_path):
    #while True:
        log_files = get_new_logs(folder_path)
        if log_files:
            log_files_data = get_health_data(log_files)
            default_dictionary = init_default_dict(log_files_data)
            current_status = update_default_dict(log_files_data, default_dictionary)
            return current_status
        #else:
        #    print("No new files")
        #
        #time.sleep(60) # poll the main folder to check for new logs 


