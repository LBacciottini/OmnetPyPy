"""
plot the congestion window from ./out/congestion_window_vector.csv as a function of time (ms)
there is only one flow
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

if __name__ == "__main__":
    df = pd.read_csv("./out/congestion_window_vector.csv")
    df["timestamp"] = df["timestamp"]/1e3  # convert to ms

    fig, ax = plt.subplots()
    ax.plot(df["timestamp"], df["sample"], label="congestion window")

    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Congestion Window Size")
    ax.set_title("Congestion Window and Latency as a function of time")

    # read also the file "latency_vector.csv" and plot a moving average of latency as a function of time in the same plot
    df_lat = pd.read_csv("./out/latency_vector.csv")

    # Compute the sliding window average
    window_size_time_units = 100

    # create a new column with the sliding window index
    df_lat["sw_index"] = df_lat["timestamp"] // window_size_time_units

    # compute the sliding window average
    sw_avg = df_lat.groupby("sw_index").mean()

    # divide the timestamp and the sample by 1e3 to have ms
    sw_avg["timestamp"] /= 1e3
    sw_avg["sample"] /= 1e3

    ax2 = ax.twinx()
    ax2.plot(sw_avg["timestamp"], sw_avg["sample"], color="red", label="latency")
    ax2.set_ylabel("Latency (ms)")

    """
    # we add a third axis to plot the throughput, again as a moving average
    throughput_window_size_time_units = 1000
    ax3 = ax.twinx()
    df_throughput = pd.read_csv("./out/throughput_vector.csv")
    df_throughput["sw_index"] = df_throughput["timestamp"] // throughput_window_size_time_units
    sw_avg_throughput = df_throughput.groupby("sw_index").count()
    sw_avg_throughput["sample"] /= throughput_window_size_time_units  # pairs per ms

    ax3.plot(sw_avg_throughput.index, sw_avg_throughput["sample"], color="green", label="throughput")
    """

    # print the legends within the axis
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    # lines3, labels3 = ax3.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc="upper right")

    # save the plot
    plt.savefig("./out/congestion_window_and_latency.pdf")

    plt.show()


