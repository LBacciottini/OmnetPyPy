"""
Print a plot of the queuing_time_vector.csv file as a sliding window average with window size 1000 time units.
"""

import pandas as pd
import matplotlib.pyplot as plt

# Load the data
df = pd.read_csv("./out/queuing_time_vector.csv")

# Compute the sliding window average
window_size_time_units = 100

# create a new column with the sliding window index
df["sw_index"] = df["timestamp"] // window_size_time_units

# compute the sliding window average
sw_avg = df.groupby("sw_index").mean()

# plot the sliding window average
plt.plot(sw_avg["sample"])
plt.xlabel("Time (us)")
plt.ylabel("Queuing time (us)")
plt.title("Moving average of queuing time")

plt.show()
