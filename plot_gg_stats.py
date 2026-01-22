import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np

# Read the CSV file
def create_monthly_land_cover_plot(csv_path='monthly_stats.csv', output_path='monthly_land_cover.png'):
    # Read the data
    df = pd.read_csv(csv_path)
    
    # Drop the index column if it exists (unnamed column)
    if df.columns[0] == 'Unnamed: 0' or df.columns[0] == '':
        df = df.drop(df.columns[0], axis=1)
    
    # Select only the columns we want (excluding "water reflection", "rock", "markers", "other")
    excluded_columns = ['water reflection', 'rock', 'markers', 'other']
    cols_to_use = [col for col in df.columns if col not in excluded_columns]
    df = df[cols_to_use]
    
    # Capitalize month names
    df['month'] = df['month'].str.capitalize()
    
    # Define a custom order for months
    month_order = {'June': 1, 'July': 2, 'August': 3, 'September': 4}
    df['month_order'] = df['month'].map(month_order)
    df = df.sort_values('month_order')
    df = df.drop('month_order', axis=1)
    
    # Set up the colors
    colors = {
        'background': '#000000',
        'cyano - dominated': '#1CE6FF',
        'lichen': '#ffdb0c',
        'moss': '#FF4A46',
        'vascular plants': '#008941',
        'snow': '#8FB0FF'
    }
    
    # Set up the figure and axes
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Get the months and classes
    months = df['month'].tolist()
    classes = [col for col in df.columns if col != 'month']
    
    # Set width of bars
    bar_width = 0.15
    
    # Set positions of bars on X axis
    r = np.arange(len(months))
    
    # Create bars for each class
    for i, cls in enumerate(classes):
        bars = ax.bar(
            r + i * bar_width - (len(classes) - 1) * bar_width / 2, 
            df[cls], 
            width=bar_width,
            label=cls.capitalize(),
            color=colors.get(cls, f'C{i}')
        )
        
        # Add values on top of bars
        for bar in bars:
            height = bar.get_height()
            if height > 2:  # Only show label if value is significant enough
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height + 1,
                    f'{height:.1f}',
                    ha='center', va='bottom',
                    rotation=90, fontsize=8
                )
    
    # Add labels, title and legend
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Percentage (%)', fontsize=12)
    ax.set_title('Monthly Distribution of Land Cover Classes', fontsize=16, fontweight='bold')
    ax.set_xticks(r)
    ax.set_xticklabels(months)
    ax.set_ylim(0, 70)  # Set y-axis limit to 70%
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
    
    # Format y-axis as percentage
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    
    # Add grid lines for better readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adjust layout and save the figure
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    # Show the plot
    plt.show()
    
    print(f"Plot saved as {output_path}")

# Call the function
if __name__ == "__main__":
    create_monthly_land_cover_plot()