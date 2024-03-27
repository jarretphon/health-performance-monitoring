import re
import streamlit as st
import numpy as np
from datetime import datetime

# get numerical value from storage represented by units i.e 70 from 70gb
def extract_numeric(storage_string):
    numerical_value = re.search(r'\d+', storage_string)
    if numerical_value:
        return float(numerical_value.group())
    else:
        return None


@st.cache_data()
def get_hdd_storage(current_status):
    hdds_storage = []
    for _, sub_module in current_status.items():
        for sub_module, sub_module_info in sub_module.items():
            if "check_hdd" in sub_module:
                hdd_info = sub_module_info

                for hdd in hdd_info:
                    for disk, data in hdd.items():
                        storage = data["storage"]
                        hdd_storage = list(map(extract_numeric, storage.split("|")))
                        hdds_storage.append(hdd_storage)
    return hdds_storage                  


def get_services_status(current_status, service):
    for module, sub_module in current_status.items():
        for sub_module, sub_module_info in sub_module.items():
            if service in sub_module:
                return sub_module_info
                

@st.cache_data()
def get_module_status(current_status):
    module_status = [{module: sub_module["status"]} for module, sub_module in current_status.items() if module != "server"]
    return module_status


def get_date_range(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT MIN(DATE(timestamp)), MAX(DATE(timestamp)) FROM HEAL_archive;")
    minmax_dates = cursor.fetchall()
    earliest_date, latest_date = minmax_dates[0]
    cursor.close()
    return earliest_date, latest_date


@st.cache_data()
def selected_hdd(server, partition, server_options, partition_options):
    if server == "All":
        server_options.remove("All")
        selected_servers = [server.replace("Server 1", "ip=10.0.0.1") if server == "Server 1" else server.replace("Server 2", "ip=10.0.0.2") for server in server_options]
    else:
        selected_servers = [server.replace("Server 1", "ip=10.0.0.1") if server == "Server 1" else server.replace("Server 2", "ip=10.0.0.2")]
    
    if partition == "All":
        partition_options.remove("All")
        selected_partitions = partition_options
    else:
        selected_partitions = [partition]

    selected_hdds = []
    for selected_server in selected_servers:
        for selected_partition in selected_partitions:
            hdd = f"{selected_server}|{selected_partition}"
            selected_hdds.append(hdd)

    return selected_hdds


@st.cache_data()
def get_storage_history(all_storage_history, selected_hdds):
    storage_history_data = {}
    for storage_history in all_storage_history:
        timestamp, hdd_storage_info = storage_history
        server_ip, partition, used, available = hdd_storage_info.split("|")
        
        hdd = f"{server_ip}|{partition}"

        if hdd in selected_hdds:
            used, available = list(map(extract_numeric, [used, available]))
            used_storage = round(used/(used+available)*100, 2)

            if hdd not in storage_history_data:
                storage_history_data[hdd] = {"datetime": [], "storage_used": []}

            storage_history_data[hdd]["datetime"].append(timestamp)
            storage_history_data[hdd]["storage_used"].append(used_storage)

    return storage_history_data


def predict_full(x_values, y_values):

    timestamps = np.array([dt.timestamp() for dt in x_values])

    gradient, intercept = np.polyfit(timestamps, y_values, deg=1)
    full_storage = 100.0
    date_timestamp = ((full_storage - intercept)/gradient)
    date = datetime.fromtimestamp(date_timestamp)
    return date

#x = [datetime(2024, 2, 29, 13, 16, 23), datetime(2024, 3, 1, 13, 16, 23), datetime(2024, 3, 2, 13, 16, 23), datetime(2024, 3, 3, 13, 16, 23), datetime(2024, 3, 4, 13, 16, 23)]
#y = [15, 16.05, 17.5, 18.65, 20]
#
#date = predict_full(x, y)
#print(date)


def get_services_history(services_status_history):
    data = {}
    for service_history in services_status_history:
        msg, timestamp, service_func, server_ip =  service_history

        key = f"{service_func}|{server_ip}" if service_func == "check_db" else service_func

        if key not in data:
            data[key] = {"dates": [], "status_type": []}

        data[key]["dates"].append(timestamp)
        data[key]["status_type"].append(msg)
    return data


def get_service_func(selected_services, services_name_w_func):
    selected_service_func = []
    for selected_service in selected_services:
        for s_name, s_func in services_name_w_func:
            if selected_service == s_name:
                selected_service_func.append((s_func))
    return selected_service_func