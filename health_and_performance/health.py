import streamlit as st
import pandas as pd
import mariadb
import numpy as np
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
import time
from threading import Thread
from data import check_for_new_logs, folder_path
from util import selected_hdd, get_date_range, get_hdd_storage, get_services_status, get_module_status, get_storage_history, get_services_history, get_service_func
from visualisation import draw_donut_chart, status_indicator, create_module, draw_storage_graph, draw_service_status_graph, style_df, highlight_errors

st.set_page_config(page_title="Health Dashboard", layout="wide")

with open("style.css", "r") as f:
    css = f.read()
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

current_status = check_for_new_logs(folder_path)

connection = mariadb.connect(host="localhost", user="HEAL_history_admin", password="Jp670525!", database="HEAL_history")

# limit date input options to available data
earliest_date, latest_date = get_date_range(connection)

server_col, service_col, module_col = st.columns([30, 35, 35])

with server_col:
    overview_container = st.container(border=True)
    storage_container = st.container(border=True)
    extrapolation_container = st.container(border=True)

    servers = ["ip=10.0.0.1", "ip=10.0.0.2"]
    partitions = ["/dev/sda", "/dev/sdb"]

    # overview of server status and hard disk storage
    with overview_container:
        servercols = st.columns(len(servers))
        for index, server in enumerate(servers):
            with servercols[index]:
                status = current_status["server"][server]["status"]
                server = st.container(border=True)
                server.write(f"Server {index+1}: {status_indicator(status)}", unsafe_allow_html=True)
        
        cols = st.columns(len(servers) * len(partitions))
        hdds_storage = get_hdd_storage(current_status)
        for i, server in enumerate(servers):
            for j, partition in enumerate(partitions):

                col_index = i * len(partitions) + j

                with cols[col_index]:
                    with st.container(border=True):      
                        used_storage, remaining_storage = hdds_storage[col_index]
                        fig = draw_donut_chart(used_storage, remaining_storage)
                        st.write(partition)
                        st.pyplot(fig, use_container_width=True)
                                      
                        
    # Graph of hard disk storage against time
    with storage_container:
        server_options = ["All", "Server 1", "Server 2"]
        partition_options = ["All", "/dev/sda", "/dev/sdb"]

        cols = st.columns(4)
        server = cols[0].selectbox("Servers", options = server_options)
        partition = cols[1].selectbox("Partitions", options = partition_options)
        start_date = cols[2].date_input("From:", format="YYYY/MM/DD", key="server_from",value=earliest_date, min_value=earliest_date, max_value=latest_date)
        end_date = cols[3].date_input("To:", format="YYYY/MM/DD", key="server_to",value=latest_date, min_value=earliest_date, max_value=latest_date)
        
        # Get hard disk storage history from database for plotting 
        cursor = connection.cursor()
        cursor.execute("SELECT timestamp, message FROM HEAL_archive WHERE sub_module_name = %s AND DATE(timestamp) BETWEEN %s AND %s ORDER BY timestamp ASC", ("check_hdd", start_date, end_date))
        all_storage_history = cursor.fetchall()
        cursor.close()

        # Graph user selected data
        selected_hdds = selected_hdd(server, partition, server_options, partition_options) 
        storage_history_data = get_storage_history(all_storage_history, selected_hdds)
        storage_graph, full_storage_dates = draw_storage_graph(storage_history_data)
        st.pyplot(storage_graph)

    # Linear regression to extrapolate estimated full hardisk capacity based on current usage
    with extrapolation_container:
        st.write("Anticipated full disk capacity dates @ current usage:")
        cols = st.columns(len(full_storage_dates))
        for index, (hdd, storage_metric) in enumerate(full_storage_dates.items()):
            date = storage_metric["date"]
            delta = str(storage_metric["storage_delta"]) + "%"
            formated_date = date.strftime("%d %B %Y")
            with cols[index]:
                metric_container = st.container(border=True)
                metric_container.metric(hdd, formated_date, delta)

with service_col:

    services = ["MariaDB 1", "MariaDB 2", "HTTP", "rabbitMQ", "Streamlit", "Uvicorn"]
    services_func = ("check_rabbit", "check_db", "check_uvicorn", "check_http", "check_streamlit")
    icons = ["rabbitmq", "mariadb", "uvicorn", "http", "streamlit"]
            
    service_overview_container = st.container(border=True)
    with service_overview_container:
    
        cols = st.columns(6)
        index = 0
        for service, icon in list(zip(services_func, icons)):
            sub_module_info = get_services_status(current_status, service)

            for info in sub_module_info:
                status = list(info.values())[0]["status"]
                with cols[index]:
                    service_container = st.container()
                    service_container.image(f"./icons/{icon}.png")
                    service_container.write(f"Status: {status_indicator(status)}", unsafe_allow_html=True)
                index+=1

    service_status_container = st.container(border=True)
    with service_status_container:

        cols = st.columns([60, 20, 20])
        selected_services = cols[0].multiselect("Select services", options=services, default=services)
        start_date = cols[1].date_input("From:", format="DD/MM/YYYY", key="service_from", value=earliest_date, min_value=earliest_date, max_value=latest_date)
        end_date = cols[2].date_input("To:", format="DD/MM/YYYY", key="service_to", value=latest_date, min_value=earliest_date, max_value=latest_date)
        
        # fetch status history from DB
        cursor = connection.cursor()
        cursor.execute("SELECT type, timestamp, sub_module_name, message FROM HEAL_archive WHERE sub_module_name in (%s, %s, %s, %s, %s) AND DATE(timestamp) BETWEEN %s AND %s ORDER BY sub_module_name, message, timestamp ASC", (*services_func, earliest_date, latest_date))
        services_status_history = cursor.fetchall()
        cursor.close()

        # process data and plot graph
        data = get_services_history(services_status_history)
        service_name_w_func = list(zip(services, list(data.keys())))
        selected_service_func = get_service_func(selected_services, service_name_w_func)
        fig = draw_service_status_graph(data, selected_service_func)
        st.pyplot(fig)

    service_perf_container = st.container(border=True)
    with service_perf_container:
        cols = st.columns(2)
        cols[0].write("Services response time")
        cols[0].selectbox("Select App", options=["SR01", "ET01"])
        cols[0].metric("DB Latency", value="0.002ms", delta="0.0032")
        cols[0].metric("Queue Latency", value="0.102ms", delta="0.0057")

        cols[1].write("API response time")
        cols[1].selectbox("Select App", options=["ET01", "VN01"])
        cols[1].metric("dbip Latency", value="0.002ms", delta="0.0032")
        cols[1].metric("mt Latency", value="0.102ms", delta="0.0057")
        cols[1].metric("kc Latency", value="0.102ms", delta="0.0057")

modules = []
modules_per_row = 9

with module_col:
    module_overview = st.container(border=True)
    with module_overview:   
        st.write("Modules")
        module_status_list = get_module_status(current_status)

        # separate the list of modules to be displayed into rows
        sublists = [module_status_list[i:i+modules_per_row] for i in range(0, len(module_status_list), modules_per_row)]
        for sublist in sublists:
            cols = st.columns(modules_per_row)
            for index, module in enumerate(sublist):
                module_name = list(module.keys())
                module_name_no_prefix = module_name[0].split("_")[1]
                modules.append(module_name_no_prefix)
                status = list(module.values())
                with cols[index]:
                    module_container = cols[index].container(border=False)
                    module_container.write(create_module(module_name_no_prefix, status[0]), unsafe_allow_html=True)


    module_info = st.container(border=True)
    with module_info:
        cols = st.columns([20, 45, 17.5, 17.5])

        module = cols[0].selectbox("Select Apps", options=modules)
        start_date = cols[2].date_input("From:", format="YYYY/MM/DD", key="module_from", value=earliest_date, min_value=earliest_date, max_value=latest_date)
        end_date = cols[3].date_input("To:", format="YYYY/MM/DD", key="module_to", value=latest_date, min_value=earliest_date, max_value=latest_date)

        # query user selected module history by date range 
        module_name = f"HEAL_{module}"
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM HEAL_archive WHERE module_ID = %s AND DATE(timestamp) BETWEEN %s AND %s ORDER BY timestamp DESC", (module_name, start_date, end_date))
        module_history_log = cursor.fetchall()
        cursor.close()

        # present history as dataframe
        module_history_data = {
            "Status": [log[1] for log in module_history_log],
            "Timestamp": [log[2] for log in module_history_log],
            "Module ID": [log[3] for log in module_history_log],
            "Sub Module": [log[4] for log in module_history_log],
            "Message": [log[6] for log in module_history_log],
        }
        df = pd.DataFrame(module_history_data)

        # warning and error msgs are highlighted for easy reference
        styled_df = df.style.apply(style_df).map(highlight_errors, subset=["Status"])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        st.divider()

        st.write("app response time")
        app_response_container = st.container(border=True)
        with app_response_container:
            cols = st.columns(3)
            cols[0].metric("myfunc", value="0.002ms", delta="0.0032")
            cols[1].metric("myfunc2", value="0.102ms", delta="0.0057")
            cols[2].metric("myfunc3", value="0.102ms", delta="0.0057")

        st.write("app usage")
        data = {
            "module": ["ET01"],
            "timestamp": ["2024-03-04 13:33:23,451"],
            "usage_history": ["column config line"]
        }
        st.dataframe(pd.DataFrame(data).style.apply(style_df), hide_index=True, use_container_width=True)