import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if __name__ == "__main__":
    # Sample data
    data = {
        'Fidelity': [0.99, 0.98, 0.97, 0.96, 0.95],
        'Latency': [100, 150, 200, 250, 300], # milliseconds
        'Queue Size (non congested)': [0.1, 0.15, 0.2, 0.25, 0.3], # num of requests
        'Queue Size (bottleneck link)': [10, 15, 20, 25, 30] # num of requests
    }

    # replace the sample data with the data from the csv files
    df_latency = pd.read_csv("./out/latency_vector.csv")
    df_latency["sample"] /= 1e3  # ms
    # compute boxplot data for latency, i.e. the 5th, 25th, 50th, 75th, 95th percentiles and the mean
    latency_boxplot_data = df_latency["sample"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    data['Latency'] = latency_boxplot_data[['5%', '25%', '50%', '75%', '95%']]

    df_fid = pd.read_csv("./out/fidelity_vector.csv")
    # compute boxplot data for fidelity, i.e. the 5th, 25th, 50th, 75th, 95th percentiles and the mean
    fidelity_boxplot_data = df_fid["sample"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    data['Fidelity'] = fidelity_boxplot_data[['5%', '25%', '50%', '75%', '95%']]

    df_queue_size_unc = pd.read_csv("./out/queue_size_free_vector.csv")
    # compute boxplot data for SKR, i.e. the 5th, 25th, 50th, 75th, 95th percentiles and the mean
    qs_unc_boxplot_data = df_queue_size_unc["sample"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    data['Queue Size (uncongested link)'] = qs_unc_boxplot_data[['5%', '25%', '50%', '75%', '95%']]

    df_queue = pd.read_csv("./out/queue_size_vector.csv")
    # compute boxplot data for throughput, i.e. the 5th, 25th, 50th, 75th, 95th percentiles and the mean
    queue_boxplot_data = df_queue["sample"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    data['Queue Size (bottleneck link)'] = queue_boxplot_data[['5%', '25%', '50%', '75%', '95%']]

    df = pd.DataFrame(data)

    # Creating faceted plots
    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(6, 6))
    # fig.suptitle('Box Plots')

    # Fidelity
    df.boxplot(column=['Fidelity'], ax=axes[0, 0])
    axes[0, 0].set_title('Fidelity')

    # Latency
    df.boxplot(column=['Latency'], ax=axes[0, 1])
    axes[0, 1].set_title('Latency (ms)')

    # QSU
    df.boxplot(column=['Queue Size (uncongested link)'], ax=axes[1, 0])
    axes[1, 0].set_title('Queue Size (uncongested link)')

    # QSB
    df.boxplot(column=['Queue Size (bottleneck link)'], ax=axes[1, 1])
    axes[1, 1].set_title('Queue Size (bottleneck link)')

    # now we also highlight the sample mean
    mean_latency = df_latency["sample"].mean()
    mean_fidelity = df_fid["sample"].mean()
    mean_qsu = df_queue_size_unc["sample"].mean()
    mean_queue = df_queue["sample"].mean()

    # plot the mean as a red dot in the boxplot
    axes[0, 0].plot(1, mean_fidelity, 'ro', label="sample mean")
    axes[0, 0].legend(loc="lower right")
    # axes[0, 0].set_ylim(0.96, 1)
    axes[0, 1].plot(1, mean_latency, 'ro', label="sample mean")
    # axes[0, 1].set_ylim(0, 1.25)
    axes[0, 1].legend(loc="upper right")
    axes[1, 0].plot(1, mean_qsu, 'ro', label="sample mean")
    axes[1, 0].axhline(y=10, color='magenta', linestyle='--', label="reference queue size")
    axes[1, 0].set_ylim(0, 40)
    axes[1, 0].legend(loc="upper right")
    axes[1, 1].plot(1, mean_queue, 'ro', label="sample mean")
    axes[1, 1].axhline(y=10, color='magenta', linestyle='--', label="reference queue size")
    axes[1, 1].set_ylim(0, 40)
    # axes[1, 1].legend(loc="upper right")

    plt.tight_layout() # Adjust the layout to make room for the main title

    # save the plot and make sure it is not cut off
    plt.savefig("./out/boxplots.pdf", bbox_inches='tight')

    plt.show()
