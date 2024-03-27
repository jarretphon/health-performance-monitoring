from matplotlib import pyplot as plt
import matplotlib.image as mpimg
import matplotlib.lines as mlines
import mplcursors
import streamlit as st
from datetime import datetime
import numpy as np

# Hdd storage stats
@st.cache_data(show_spinner=True)
def draw_donut_chart(used, remaining):
    sizes = [used, remaining]
    colors = ['#ff8080', '#66b3ff']

    fig2, ax2 = plt.subplots(figsize=(1, 1), dpi=10, facecolor="#002B36")
    ax2.pie(sizes, colors=colors, startangle=90, autopct='%1.2f%%', textprops={'color': "#FAFAFA", "fontsize": 12, "fontweight": 700}, wedgeprops=dict(width=0.25), pctdistance=0.7)
    ax2.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    # Draw a  circle in the center to create the donut chart
    centre_circle = plt.Circle((0, 0), 0.8, color=(0/255, 43/255, 54/255), alpha=0.1)  # Transparent background
    ax2.add_artist(centre_circle)

    # Load the hard disk icon image
    color = "green" if used/(used+remaining) <= 0.6 else "orange" if 0.6 < used/(used+remaining) < 0.8 else "red"
    hdd_icon = mpimg.imread(f"./icons/icons8-server-storage-48-{color}.png")  # Replace with the path to your HDD icon image

    # Plot the hard disk icon within the donut chart
    ax2.imshow(hdd_icon, extent=(-0.4, 0.4, -0.4, 0.4), aspect='equal', zorder=1)

    # Hide axes
    ax2.axis('off')

    return fig2


@st.cache_data()
def status_indicator(status):
    color = "#FF6347" if status in ["ERROR", "CRITICAL"] else "#FFA500" if status == "WARNING" else "#32CD32"
    statusHTML =f"""
        <div style="background-color: {color}; border-radius: 20%; width: 25px; height: 15px; margin-left: 1em; display: inline-block;"></div>
    """
    return statusHTML


@st.cache_data()
def create_module(module_name, status):
    color = "red" if status in ["ERROR", "CRITICAL"] else "orange" if status == "WARNING" else "green"
    moduleHTML = f"""
        <div style="background-color: {color}; border: 2px solid rgb(88, 110, 117); width: 100%; text-align: center; padding: 0.5em; margin-bottom: 0.75em; border-radius: 0.5em; font-family: monospace; overflow-wrap: break-word;">
            {module_name}
        </div>
    """
    return moduleHTML


def predict_full(x_values, y_values):

    timestamps = np.array([dt.timestamp() for dt in x_values])

    gradient, intercept = np.polyfit(timestamps, y_values, deg=1)
    full_storage = 100.0
    date_timestamp = ((full_storage - intercept)/gradient)
    date = datetime.fromtimestamp(date_timestamp)
    
    storage_delta = y_values[-1] - y_values[-2]

    return date, storage_delta


@st.cache_data()
def draw_storage_graph(storage_data):
    with plt.style.context('Solarize_Light2'):
        fig, ax = plt.subplots(figsize=(8, 4))

        storage_metrics = {}
        for hdd, storage_info in storage_data.items():
            ax.plot(storage_info["datetime"], storage_info["storage_used"], label=hdd, linewidth=2, marker="o", markersize=5)
            ax.fill_between(storage_info["datetime"], storage_info["storage_used"], alpha=0.4)

            # extrapolating the graph based on data to determine estimated date od full capacity
            full_storage_date, storage_delta = predict_full(storage_info["datetime"], storage_info["storage_used"])
            if hdd not in storage_metrics:
                storage_metrics[hdd] = {"date": full_storage_date, "storage_delta": round(storage_delta, 2)}

        ax.set_title("Hard Disk Storage", color="#FAFAFA")
        ax.set_xlabel("Date", color="#FAFAFA")
        ax.set_ylabel("Storage (%)", color="#FAFAFA", rotation=0)
        ax.set_ylim(0, 100)
        ax.set_yticks(range(0,101,10))
        ax.grid(color='#586e75', linestyle='-', linewidth=0.35, alpha=0.9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.legend(fontsize=7, loc="upper left", framealpha=0.5)

        fig.autofmt_xdate(rotation=45)
        ax.set_facecolor("#002b36")
        fig.set_facecolor("#002b36")
        ax.xaxis.set_label_coords(0.98, 0.06)
        ax.yaxis.set_label_coords(0.00, 1.05)
    return fig, storage_metrics


@st.cache_data()
def draw_service_status_graph(data, selected_service_func):
    with plt.style.context('Solarize_Light2'):
            
        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(8, 4))

        for service_func, service_status_hist in data.items():
            if service_func in selected_service_func:
                x_values = service_status_hist["dates"]
                y_values = [0] * len(x_values)

                # Plot the horizontal line segment by segment
                for i in range(len(x_values) - 1):
                    start_date = x_values[i]
                    end_date = x_values[i + 1]
                    status_type = service_status_hist['status_type'][i]
                    
                    # Set color based on status type
                    color = '#FF6347' if status_type in ["CRITICAL", "ERROR"] else '#FFA500' if status_type == "WARNING" else '#32CD32'

                    # legend labels
                    green_line = mlines.Line2D([], [], color='#32CD32', marker='|', markersize=8, linewidth=5, label="INFO/DEBUG")
                    red_line = mlines.Line2D([], [], color='#FF6347', marker='|', markersize=8, linewidth=5, label="ERROR/CRITICAL")
                    orange_line = mlines.Line2D([], [], color='#FFA500', marker='|', markersize=8, linewidth=5, label="WARNING")

                    # Plot line segment
                    ax.plot([start_date, end_date], [f"{service_func}", f"{service_func}"], color=color, linewidth=5, marker="|", markersize=8, solid_capstyle="round")

                # Add labels and title
                ax.set_xlabel('Date', color="#FAFAFA")
                ax.set_ylabel('Services',color="#FAFAFA", rotation = 0)
                ax.set_title('Status History', color="#FAFAFA")      
                ax.grid(color='#586e75', linestyle='-', linewidth=0.25, alpha=0.7)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.legend(handles=[green_line, orange_line, red_line], fontsize=7, framealpha=0.5, bbox_to_anchor=(0, -0.025))

                fig.autofmt_xdate(rotation=45)
                ax.set_facecolor("#002b36")
                fig.set_facecolor("#002b36")
                ax.xaxis.set_label_coords(0.98, 0.06)
                ax.yaxis.set_label_coords(0.00, 1.05)   
    return fig


def style_df(col):
    return ['background-color: #586e75; color: #FAFAFA' for _ in col]


def highlight_errors(type):
    color = "#d9822b" if type == "WARNING" else ("#9c4232" if type in ["ERROR", "CRITICAL"] else "#586e75")
    return f'background-color: {color}'