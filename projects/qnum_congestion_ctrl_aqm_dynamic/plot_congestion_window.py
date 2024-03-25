"""
plot the congestion window from ./out/congestion_window_vector.csv as a function of time (ms)
there is only one flow
"""
import math

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def compute_fid(latency, gamma):
    """
    Compute the flow id from the latency and the gamma parameter
    """
    return 0.5 + 0.5*math.exp(-2*gamma*latency)

if __name__ == "__main__":

    fig, ax = plt.subplots()
    """
    ax.plot(df["timestamp"], df["sample"], label="congestion window")
    """

    ax.set_xlabel("Time (ms)")
    # ax.set_ylabel("Congestion Window Size")
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Latency with increasing load")

    # read also the file "latency_vector.csv" and plot a moving average of latency as a function of time in the same plot
    df_lat = pd.read_csv("./out/latency_vector.csv")

    # Compute the sliding window average
    window_size_time_units = 100000

    # create a new column with the sliding window index
    df_lat["sw_index"] = df_lat["timestamp"] // window_size_time_units

    # compute the sliding window average
    sw_avg = df_lat.groupby("sw_index").mean()

    # divide the timestamp and the sample by 1e3 to have ms
    sw_avg["timestamp"] /= 1e3
    sw_avg["sample"] /= 1e3

    # ax2 = ax.twinx()
    ax.plot(sw_avg["timestamp"], sw_avg["sample"], color="red", label="latency")
    # ax.set_ylabel("Latency (ms)")

    cur_flows = 4
    for i in range(0, 24000, 8000):
        ax.axvline(x=i, color='r', linestyle=':', alpha=0.2)
        # add some text next to the line saying "2 flows added" at the top
        ax.text(i + 100, 10, f"{cur_flows} flows", rotation=90, fontsize=6)
        cur_flows += 6

    """
    # read the IRG file and plot the Inter-Request Gap (IRG) on the same plot but on a different axis
    df_irg = pd.read_csv("./out/IRG_vector.csv")
    df_irg["sw_index"] = df_irg["timestamp"] // window_size_time_units
    sw_avg_irg = df_irg.groupby("sw_index").mean()
    sw_avg_irg["timestamp"] /= 1e3
    sw_avg_irg["sample"] /= 1e3
    
    ax2 = ax.twinx()
    ax2.plot(sw_avg_irg["timestamp"], sw_avg_irg["sample"], color="blue", label="IRG")
    ax2.set_ylabel("IRG (ms)")
    """

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
    """
    df_fid = sw_avg
    df_fid["fid"] = df_fid.apply(lambda row: compute_fid(row["sample"], 0.01), axis=1)
    ax2 = ax.twinx()
    ax2.plot(df_fid["timestamp"], df_fid["fid"], color="green", label="Fidelity")
    ax2.set_ylabel("Fidelity")
    """


    # print the legends within the axis

    lines, labels = ax.get_legend_handles_labels()
    # lines2, labels2 = ax2.get_legend_handles_labels()
    # lines3, labels3 = ax3.get_legend_handles_labels()
    # ax2.legend(lines + lines2, labels + labels2, loc="upper right")

    # print legend in the axis box
    ax.legend(lines, labels, loc="upper right")

    # save the plot
    plt.savefig("./out/latency_dynamic.pdf")

    plt.show()

