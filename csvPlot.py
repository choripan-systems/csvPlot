import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import argparse

def plot_csv_data(csv_file):
    """
    Read CSV file and create an interactive plot with click-drag zoom.
    
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
        plt.subplots_adjust(bottom=0.15)
        
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
        ax.set_title(f'Data from {csv_file}\n(Click and drag to zoom, Right-click to reset)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Set initial limits with some padding
        initial_xlim = (x_min - 0.05 * x_range, x_max + 0.05 * x_range)
        initial_ylim = (y_min - 0.05 * y_range, y_max + 0.05 * y_range)
        ax.set_xlim(initial_xlim)
        ax.set_ylim(initial_ylim)
        
        # Variables for selection rectangle
        selection_rect = None
        start_x = None
        is_dragging = False
        
        def on_press(event):
            """Handle mouse button press"""
            nonlocal start_x, is_dragging, selection_rect
            
            if event.inaxes != ax:
                return
            
            # Right click resets the view
            if event.button == 3:
                ax.set_xlim(initial_xlim)
                ax.set_ylim(initial_ylim)
                fig.canvas.draw()
                return
            
            # Left click starts selection
            if event.button == 1:
                start_x = event.xdata
                is_dragging = True
                
                # Remove old selection rectangle if it exists
                if selection_rect is not None:
                    selection_rect.remove()
                    selection_rect = None
                
        def on_motion(event):
            """Handle mouse motion"""
            nonlocal selection_rect
            
            if not is_dragging or event.inaxes != ax or start_x is None:
                return
            
            # Remove old rectangle
            if selection_rect is not None:
                selection_rect.remove()
            
            # Draw new selection rectangle
            current_x = event.xdata
            ylim = ax.get_ylim()
            
            rect_x = min(start_x, current_x)
            rect_width = abs(current_x - start_x)
            rect_y = ylim[0]
            rect_height = ylim[1] - ylim[0]
            
            selection_rect = Rectangle(
                (rect_x, rect_y), 
                rect_width, 
                rect_height,
                fill=True,
                facecolor='blue',
                alpha=0.2,
                edgecolor='blue',
                linewidth=2
            )
            ax.add_patch(selection_rect)
            fig.canvas.draw()
        
        def on_release(event):
            """Handle mouse button release"""
            nonlocal is_dragging, selection_rect, start_x
            
            if not is_dragging or event.inaxes != ax or start_x is None:
                is_dragging = False
                return
            
            is_dragging = False
            end_x = event.xdata
            
            if end_x is None:
                return
            
            # Remove selection rectangle
            if selection_rect is not None:
                selection_rect.remove()
                selection_rect = None
            
            # Zoom to selected region
            new_xlim = (min(start_x, end_x), max(start_x, end_x))
            
            # Only zoom if selection is meaningful (not just a click)
            if abs(end_x - start_x) > 0.01 * x_range:
                ax.set_xlim(new_xlim)
                fig.canvas.draw()
            
            start_x = None
        
        # Add annotation for hover display
        annot = ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                           bbox=dict(boxstyle="round", fc="yellow", alpha=0.9),
                           arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def on_hover(event):
            """Handle mouse hover to show data point values"""
            if event.inaxes != ax or is_dragging:
                annot.set_visible(False)
                fig.canvas.draw_idle()
                return
            
            # Check each line to see if cursor is near a data point
            for line, col_name in zip(lines, y_columns):
                contains, ind = line.contains(event)
                if contains:
                    # Get the index of the point
                    index = ind["ind"][0]
                    x_val = x_data.iloc[index]
                    y_val = df[col_name].iloc[index]
                    
                    # Update annotation
                    annot.xy = (x_val, y_val)
                    text = f"{col_name}\n{x_label}: {x_val:.4g}\nY: {y_val:.4g}"
                    annot.set_text(text)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return
            
            # No point found, hide annotation
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        # Connect event handlers
        fig.canvas.mpl_connect('button_press_event', on_press)
        fig.canvas.mpl_connect('motion_notify_event', on_motion)
        fig.canvas.mpl_connect('button_release_event', on_release)
        fig.canvas.mpl_connect('motion_notify_event', on_hover)
        
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
        description='Plot data from a CSV file with interactive click-drag zoom'
    )
    parser.add_argument(
        'csv_file',
        help='Path to the CSV file to plot'
    )
    
    args = parser.parse_args()
    plot_csv_data(args.csv_file)

if __name__ == "__main__":
    main()
    