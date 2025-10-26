import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.widgets import Slider
import argparse

def plot_csv_data(csv_file, x_tick_spacing=10, y_tick_spacing=None):
    """
    Read CSV file and create an interactive plot with fixed tick spacing.
    
    Args:
        csv_file: Path to the CSV file
        x_tick_spacing: Number of data points between X-axis tick marks
        y_tick_spacing: Number of data points between Y-axis tick marks (for Y-range calculation)
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
        
        # Number of data points
        n_points = len(x_data)
        
        # Create the figure and axis
        fig, ax = plt.subplots(figsize=(12, 6))
        plt.subplots_adjust(bottom=0.2, right=0.85)
        
        # Store original data limits
        x_min, x_max = x_data.min(), x_data.max()
        
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
        ax.set_title(f'Data from {csv_file}\n(Right-click to reset view, Hover for values)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Set Y limits with some padding
        ax.set_ylim(y_min - 0.05 * y_range, y_max + 0.05 * y_range)
        
        # Setup X-axis ticks based on data point spacing
        # Generate tick positions for ALL data points at the specified interval
        tick_indices = list(range(0, n_points, x_tick_spacing))
        if tick_indices[-1] != n_points - 1:
            tick_indices.append(n_points - 1)  # Always include last point
        
        all_tick_positions = [x_data.iloc[i] for i in tick_indices]
        all_tick_labels = [f'{x_data.iloc[i]:.4g}' for i in tick_indices]
        
        ax.set_xticks(all_tick_positions)
        ax.set_xticklabels(all_tick_labels, rotation=45, ha='right')
        
        # Setup Y-axis ticks
        if y_tick_spacing:
            # Calculate how many ticks we want based on spacing
            n_y_ticks = max(2, int(n_points / y_tick_spacing) + 1)
            y_tick_step = y_range / (n_y_ticks - 1)
            y_tick_positions = [y_min + i * y_tick_step for i in range(n_y_ticks)]
            ax.set_yticks(y_tick_positions)
            ax.set_yticklabels([f'{pos:.4g}' for pos in y_tick_positions])
        
        # Calculate initial window size (show about 50 data points initially, or all if less)
        initial_window = min(50, n_points)
        window_size = initial_window
        
        # Initial X limits
        initial_xlim = (x_data.iloc[0], x_data.iloc[min(window_size - 1, n_points - 1)])
        ax.set_xlim(initial_xlim)
        
        # State variables
        current_pos = 0
        is_dragging = False
        selection_rect = None
        start_x = None
        
        # Create horizontal scroll slider
        ax_scroll = plt.axes([0.15, 0.05, 0.7, 0.03])
        max_scroll = max(0, n_points - window_size)
        scroll_slider = Slider(
            ax_scroll,
            'Scroll Position',
            0,
            max_scroll,
            valinit=0,
            valstep=1
        )
        
        def update_view(pos):
            """Update the visible window based on scroll position"""
            nonlocal current_pos
            current_pos = int(pos)
            
            # Calculate which points to show
            start_idx = current_pos
            end_idx = min(current_pos + window_size - 1, n_points - 1)
            
            # Set X limits to show this window
            x_left = x_data.iloc[start_idx]
            x_right = x_data.iloc[end_idx]
            ax.set_xlim(x_left, x_right)
            
            fig.canvas.draw_idle()
        
        def on_scroll(val):
            """Handle scroll slider movement"""
            update_view(val)
        
        scroll_slider.on_changed(on_scroll)
        
        # Add annotation for hover display
        annot = ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                           bbox=dict(boxstyle="round", fc="yellow", alpha=0.9),
                           arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def on_press(event):
            """Handle mouse button press"""
            nonlocal start_x, is_dragging, selection_rect, window_size, current_pos
            
            if event.inaxes != ax:
                return
            
            # Right click resets the view
            if event.button == 3:
                window_size = n_points
                current_pos = 0
                scroll_slider.valmax = max(0, n_points - window_size)
                scroll_slider.set_val(0)
                ax.set_xlim(x_min, x_max)
                fig.canvas.draw()
                return
            
            # Left click starts selection (for zoom)
            if event.button == 1:
                start_x = event.xdata
                is_dragging = True
                
                if selection_rect is not None:
                    selection_rect.remove()
                    selection_rect = None
        
        def on_motion(event):
            """Handle mouse motion"""
            nonlocal selection_rect
            
            if is_dragging and event.inaxes == ax and start_x is not None:
                if selection_rect is not None:
                    selection_rect.remove()
                
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
                fig.canvas.draw_idle()
        
        def on_release(event):
            """Handle mouse button release"""
            nonlocal is_dragging, selection_rect, start_x, window_size, current_pos
            
            if not is_dragging or event.inaxes != ax or start_x is None:
                is_dragging = False
                return
            
            is_dragging = False
            end_x = event.xdata
            
            if end_x is None:
                return
            
            if selection_rect is not None:
                selection_rect.remove()
                selection_rect = None
            
            x_left = min(start_x, end_x)
            x_right = max(start_x, end_x)
            
            # Find corresponding data point indices
            left_idx = (x_data - x_left).abs().argmin()
            right_idx = (x_data - x_right).abs().argmin()
            
            # Only zoom if selection is meaningful (at least 2 points)
            if right_idx - left_idx >= 1:
                window_size = right_idx - left_idx + 1
                current_pos = left_idx
                
                # Update slider
                scroll_slider.valmax = max(0, n_points - window_size)
                scroll_slider.set_val(min(current_pos, scroll_slider.valmax))
                
                ax.set_xlim(x_data.iloc[left_idx], x_data.iloc[right_idx])
                fig.canvas.draw()
            
            start_x = None
        
        def on_hover(event):
            """Handle mouse hover to show data point values"""
            if event.inaxes != ax or is_dragging:
                annot.set_visible(False)
                fig.canvas.draw_idle()
                return
            
            for line, col_name in zip(lines, y_columns):
                contains, ind = line.contains(event)
                if contains:
                    index = ind["ind"][0]
                    x_val = x_data.iloc[index]
                    y_val = df[col_name].iloc[index]
                    
                    annot.xy = (x_val, y_val)
                    text = f"{col_name}\n{x_label}: {x_val:.4g}\nY: {y_val:.4g}"
                    annot.set_text(text)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return
            
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
        description='Plot data from a CSV file with configurable tick spacing'
    )
    parser.add_argument(
        'csv_file',
        help='Path to the CSV file to plot'
    )
    parser.add_argument(
        '--x-spacing',
        type=int,
        default=10,
        help='Number of data points between X-axis tick marks (default: 10)'
    )
    parser.add_argument(
        '--y-spacing',
        type=int,
        default=None,
        help='Number of data points between Y-axis tick marks (optional)'
    )
    
    args = parser.parse_args()
    plot_csv_data(args.csv_file, args.x_spacing, args.y_spacing)

if __name__ == "__main__":
    main()
    