import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("benchmark.csv")
df.groupby("method")["duration_seconds"].mean().plot(kind="bar")
plt.show()
df.groupby("method")["latency_seconds"].mean().plot(kind="bar")
plt.show()
df.groupby("method")["memory_used_kb"].mean().plot(kind="bar")
plt.show()