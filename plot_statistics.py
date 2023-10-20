import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
# sns.set_context('talk')

df = pd.read_csv("C:\\Users\\faulhamm\\Documents\\Philipp\\code\\cc-data-processing\\microhabitats.csv")
print(df.values[0])
x_axis = ['N', 'E', 'S', 'W']
x=np.arange(len(x_axis))
fig, ax = plt.subplots(3,1, figsize=(8,10))

bar_width = 0.3
b1 = ax[2].bar(x, df.values[0][:4], width=bar_width, label="Terra firme")
b2 = ax[2].bar(x + bar_width, df.values[0][12:16], width=bar_width, label="Campina")
ax[2].set_title("Ground")

b3 = ax[1].bar(x, df.values[0][4:8], width=bar_width, label="Terra firme")
# b2 = ax[0].bar(x + bar_width, df.values[0][12:16], width=bar_width)
ax[1].set_title("Main stem")

b5 = ax[0].bar(x, df.values[0][8:12], width=bar_width, label="Terra firme")
b6 = ax[0].bar(x + bar_width, df.values[0][16:], width=bar_width, label="Campina")
ax[0].set_title("Canopy")


for a in ax:
    a.set_xticks(x + bar_width / 2)
    a.set_xticklabels(x_axis)
    a.set_ylabel('# Images', labelpad=15)
    a.legend()

ax[2].set_xlabel('Direction', labelpad=15)


plt.savefig("C:\\Users\\faulhamm\\Documents\\Philipp\\code\\cc-data-processing\\microhabitats.png", dpi=300, bbox_inches='tight')
# plt.show()