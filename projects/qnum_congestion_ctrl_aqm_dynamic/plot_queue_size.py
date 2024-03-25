"""
Read the file "queue_size_vector.csv" and plot the queue size as a function of time
"""

import pandas as pd
import matplotlib.pyplot as plt

if __name__ == "__main__":
    df = pd.read_csv("./out/queue_size_vector.csv")

    fig, ax = plt.subplots()

    # now we want to plot as a sliding window average
    window_size_time_units = 600000
    # every point in the plot is the average of all samples in the window
    # we can't use directly group by because the same sample may be in multiple adjacent windows
    # so, for every row in df, we compute the average of all samples in the window
    # we use a list comprehension to do that
    sw_avg = pd.Series([df[(df["timestamp"] >= t - window_size_time_units) & (df["timestamp"] < t)]["sample"].mean() for t in df["timestamp"]])

    df["timestamp"] = df["timestamp"] / 1e3  # convert to ms

    # multiply the sample columne by 0.04
    sw_avg *= 0.04

    ax.plot(df["timestamp"], sw_avg, label="queue size")

    # also plot a horizontal green dashed line at the reference queue size set to 20
    ax.axhline(y=10, color='g', linestyle='--', label="reference queue size")

    # also plot a vertical soft, dashed line every 3000 ms
    cur_flows = 4
    for i in range(0, 24000, 8000):
        ax.axvline(x=i, color='r', linestyle=':', alpha=0.2)
        # add some text next to the line saying "2 flows added" at the top
        ax.text(i + 100, 150, f"{cur_flows} flows", rotation=90, fontsize=6)
        cur_flows += 6



    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Queue Size")
    ax.set_title("Upstream Queue Size at node 2 over time")

    ax.legend()

    plt.show()

    # Save the figure
    fig.savefig("./out/queue_size.pdf")