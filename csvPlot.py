import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import argparse

def plot_csv_data(csv_file):
    """
    Read CSV file and create an interactive plot with zoom slider.
    
    Args:
        csv_file: Path to the CSV file
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        # Validate that we have at least 2 columns
        if len(df.columns) < 2:
            print("Error: CSV file must have at least 2 columns")
            sys.exit(1)
        
        # Extract X values (first column)
        x_data = df.iloc[:, 0]
        x_label = df.columns[0]
        
        # Get all Y columns (column 2 onwards)
        y_columns = df.columns[1:]
        
        # Create the figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))
        plt.subplots_adjust(bottom=0.25)
        
        # Store original data limits
        x_min, x_max = x_data.min(), x_data.max()
        x_range = x_max - x_min
        
        # Find global Y limits across all Y columns
        y_min = df.iloc[:, 1:].min().min()
        y_max = df.iloc[:, 1:].max().max()
        y_range = y_max - y_min
        
        # Plot all Y columns
        lines = []
        for col in y_columns:
            line, = ax.plot(x_data, df[col], label=col, marker='o', markersize=4)
            lines.append(line)
        
        # Set labels and title
        ax.set_xlabel(x_label)
        ax.set_ylabel('Values')
        ax.set_title(f'Data from {csv_file}')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Set initial limits with some padding
        ax.set_xlim(x_min - 0.05 * x_range, x_max + 0.05 * x_range)
        ax.set_ylim(y_min - 0.05 * y_range, y_max + 0.05 * y_range)
        
        # Create slider for zoom control
        ax_slider = plt.axes([0.2, 0.1, 0.6, 0.03])
        zoom_slider = Slider(
            ax_slider, 
            'Zoom', 
            0.1,  # Min zoom (10% of data)
            1.0,  # Max zoom (100% of data - full view)
            valinit=1.0,
            valstep=0.05
        )
        
        # Store the center point for zooming
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        
        def update(val):
            """Update plot based on slider value"""
            zoom = zoom_slider.val
            
            # Calculate new ranges based on zoom level
            new_x_range = x_range * zoom
            new_y_range = y_range * zoom
            
            # Set new limits centered on the data
            ax.set_xlim(center_x - new_x_range / 2, center_x + new_x_range / 2)
            ax.set_ylim(center_y - new_y_range / 2, center_y + new_y_range / 2)
            
            fig.canvas.draw_idle()
        
        # Connect slider to update function
        zoom_slider.on_changed(update)
        
        plt.show()
        
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        print(f"Error: File '{csv_file}' is empty")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)

def main():
    """Main function to parse arguments and run the plotter"""
    parser = argparse.ArgumentParser(
        description='Plot data from a CSV file with interactive zoom control'
    )
    parser.add_argument(
        'csv_file',
        help='Path to the CSV file to plot'
    )
    
    args = parser.parse_args()
    plot_csv_data(args.csv_file)

if __name__ == "__main__":
    main()
    