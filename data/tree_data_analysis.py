import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the data
def analyze_trees_graz(file_path='trees_graz.csv'):
    # Read the CSV file
    print("Loading the dataset...")
    df = pd.read_csv(file_path)
    
    # Display basic information about the dataset
    print("\n==== Dataset Overview ====")
    print(f"Shape of the dataset: {df.shape}")
    print("\nFirst 5 rows:")
    print(df.head())
    
    # Display column names (headers)
    print("\n==== Column Headers ====")
    print(df.columns.tolist())
    
    # Check data types and missing values
    print("\n==== Data Information ====")
    print(df.info())
    
    print("\n==== Statistical Summary ====")
    print(df.describe())
    
    # Tree species analysis
    print("\n==== Tree Species Analysis ====")
    # Count the number of unique tree species (using LatinName as species identifier)
    num_species = df['LatinName'].nunique()
    print(f"Number of unique tree species (Latin names): {num_species}")
    
    # Top 10 most common tree species
    print("\nTop 10 most common tree species:")
    print(df['LatinName'].value_counts().head(10))
    
    # Plot tree species distribution (top 15)
    plt.figure(figsize=(12, 8))
    df['LatinName'].value_counts().head(15).plot(kind='bar')
    plt.title('Top 15 Tree Species in Graz')
    plt.xlabel('Latin Name')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('tree_species_distribution.png')
    print("\nPlot saved as 'tree_species_distribution.png'")
    
    # Traffic zone analysis
    print("\n==== Traffic Zone Analysis ====")
    # Count trees in each traffic level
    traffic_counts = df['TrafficLevel'].value_counts()
    print("Distribution of trees by traffic level (numeric):")
    print(traffic_counts)
    
    # Using the text description for better readability
    traffic_desc_counts = df['TrafficDescription'].value_counts()
    print("\nDistribution of trees by traffic description:")
    print(traffic_desc_counts)
    
    # Visualize distribution
    plt.figure(figsize=(10, 6))
    sns.countplot(x='TrafficDescription', data=df, palette='viridis')
    plt.title('Distribution of Trees in Traffic Zones')
    plt.xlabel('Traffic Zone')
    plt.ylabel('Number of Trees')
    plt.tight_layout()
    plt.savefig('traffic_zone_distribution.png')
    print("\nPlot saved as 'traffic_zone_distribution.png'")
    
    # Species distribution across traffic zones
    print("\nTop 5 species in each traffic zone:")
    for zone in df['TrafficDescription'].unique():
        print(f"\n{zone} Traffic Zone:")
        print(df[df['TrafficDescription'] == zone]['LatinName'].value_counts().head(5))
    
    # Create a cross-tabulation
    cross_tab = pd.crosstab(df['LatinName'], df['TrafficDescription'])
    print("\nCross-tabulation of top 10 species across traffic zones:")
    print(cross_tab.head(10))
    
    # Visualize top 10 species across traffic zones
    top_species = df['LatinName'].value_counts().head(10).index
    plt.figure(figsize=(12, 8))
    crosstab_filtered = pd.crosstab(
        df[df['LatinName'].isin(top_species)]['LatinName'],
        df[df['LatinName'].isin(top_species)]['TrafficDescription']
    )
    crosstab_filtered.plot(kind='bar', stacked=True)
    plt.title('Top 10 Tree Species Distribution Across Traffic Zones')
    plt.xlabel('Latin Name')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('species_by_traffic_zone.png')
    print("\nPlot saved as 'species_by_traffic_zone.png'")
    
    # Additional analysis (age, height, diameter, etc.)
    print("\n==== Additional Analysis ====")
    
    # Age analysis based on PlantingYear
    print("\nTree age analysis:")
    
    # Calculate current year
    current_year = 2025
    
    # Filter out missing planting years
    planting_df = df[df['PlantingYear'].notna()]
    
    if not planting_df.empty:
        # Calculate age for each tree
        planting_df['Age'] = current_year - planting_df['PlantingYear']
        
        print(f"Average tree age: {planting_df['Age'].mean():.2f} years")
        print(f"Oldest tree: {planting_df['Age'].max()} years")
        print(f"Youngest tree: {planting_df['Age'].min()} years")
        
        # Age distribution histogram
        plt.figure(figsize=(10, 6))
        sns.histplot(planting_df['Age'].dropna(), kde=True, bins=20)
        plt.title('Distribution of Tree Ages')
        plt.xlabel('Age (years)')
        plt.ylabel('Count')
        plt.tight_layout()
        plt.savefig('age_distribution.png')
        print("\nPlot saved as 'age_distribution.png'")
        
        # Analyze planting trends over time
        plt.figure(figsize=(12, 6))
        planting_counts = df['PlantingYear'].value_counts().sort_index()
        planting_counts.plot(kind='bar')
        plt.title('Tree Planting Trends Over Time')
        plt.xlabel('Planting Year')
        plt.ylabel('Number of Trees Planted')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('planting_trends.png')
        print("\nPlot saved as 'planting_trends.png'")
    
    # Tree type analysis
    print("\n==== Tree Type Analysis ====")
    type_counts = df['Type'].value_counts()
    print("Distribution of tree types:")
    print(type_counts)
    
    # Visualize tree types
    plt.figure(figsize=(10, 6))
    sns.countplot(y='Type', data=df, palette='Set2')
    plt.title('Distribution of Tree Types')
    plt.xlabel('Count')
    plt.ylabel('Tree Type')
    plt.tight_layout()
    plt.savefig('tree_type_distribution.png')
    print("\nPlot saved as 'tree_type_distribution.png'")
    
    # Location analysis
    print("\n==== Location Analysis ====")
    location_counts = df['Location'].value_counts().head(15)
    print("Top 15 locations with most trees:")
    print(location_counts)
    
    # Visualize top locations
    plt.figure(figsize=(12, 8))
    location_counts.plot(kind='bar')
    plt.title('Top 15 Locations with Most Trees')
    plt.xlabel('Location')
    plt.ylabel('Number of Trees')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('location_distribution.png')
    print("\nPlot saved as 'location_distribution.png'")
    
    # Analyze tree species by location (top locations only)
    top_locations = location_counts.index.tolist()[:5]  # Top 5 locations
    print("\nTree species distribution in top 5 locations:")
    
    # Create subplot for top locations and their species distribution
    fig, axes = plt.subplots(len(top_locations), 1, figsize=(12, 4*len(top_locations)))
    
    for i, location in enumerate(top_locations):
        location_species = df[df['Location'] == location]['LatinName'].value_counts().head(5)
        print(f"\n{location}:")
        print(location_species)
        
        # Plot for each location
        if len(top_locations) > 1:
            ax = axes[i]
        else:
            ax = axes
        
        location_species.plot(kind='barh', ax=ax)
        ax.set_title(f'Top 5 Tree Species in {location}')
        ax.set_xlabel('Count')
    
    plt.tight_layout()
    plt.savefig('species_by_location.png')
    print("\nPlot saved as 'species_by_location.png'")
    
    # Analyze relationship between traffic levels and tree species diversity
    print("\n==== Traffic Level and Tree Species Diversity ====")
    # Calculate species diversity per traffic level
    diversity_by_traffic = {}
    
    for traffic in df['TrafficDescription'].unique():
        unique_species = df[df['TrafficDescription'] == traffic]['LatinName'].nunique()
        total_trees = df[df['TrafficDescription'] == traffic].shape[0]
        diversity_by_traffic[traffic] = {
            'unique_species': unique_species, 
            'total_trees': total_trees,
            'species_per_100_trees': (unique_species / total_trees) * 100
        }
    
    for traffic, stats in diversity_by_traffic.items():
        print(f"\n{traffic} Traffic Zone:")
        print(f"  Unique species: {stats['unique_species']}")
        print(f"  Total trees: {stats['total_trees']}")
        print(f"  Species per 100 trees: {stats['species_per_100_trees']:.2f}")
        
    # Visualize diversity metrics
    traffic_levels = list(diversity_by_traffic.keys())
    species_counts = [diversity_by_traffic[t]['unique_species'] for t in traffic_levels]
    tree_counts = [diversity_by_traffic[t]['total_trees'] for t in traffic_levels]
    
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    x = range(len(traffic_levels))
    ax1.bar(x, species_counts, width=0.4, align='edge', color='skyblue', label='Unique Species')
    ax1.set_ylabel('Number of Unique Species')
    ax1.set_xticks([i + 0.2 for i in x])
    ax1.set_xticklabels(traffic_levels)
    
    ax2 = ax1.twinx()
    ax2.bar([i + 0.4 for i in x], tree_counts, width=0.4, color='lightgreen', label='Total Trees')
    ax2.set_ylabel('Total Number of Trees')
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    plt.title('Tree Diversity and Count by Traffic Level')
    plt.tight_layout()
    plt.savefig('traffic_diversity.png')
    print("\nPlot saved as 'traffic_diversity.png'")

    print("\n==== Analysis Complete ====")
    return df

# Run the analysis
if __name__ == "__main__":
    df = analyze_trees_graz('trees_graz.csv')

    print(df)