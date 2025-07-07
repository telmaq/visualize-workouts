#!/usr/bin/env python3

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import termios
import tty
import os
from collections import defaultdict

class WorkoutVisualizer:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.df['Workout Start'] = pd.to_datetime(self.df['Workout Start'])
        self.exercises = sorted(self.df['Exercise'].dropna().unique())
        self.selected_index = 0

    def get_key(self):
        """Get a single keypress from terminal"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)
            if key == '\x1b':  # ESC sequence
                key += sys.stdin.read(2)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key
    
    def clear_screen(self):
        print("\033[H\033[J", end="")  # Move cursor to top-left and clear to end of screen
    
    def display_menu(self):
        """Display exercise selection menu"""
        self.clear_screen()
        print("🏋️  WORKOUT PROGRESSION VISUALIZER 🏋️")
        print("=" * 50)
        print("\nSelect an exercise to visualize:")
        print("(Use ↑/↓ arrows to navigate, Enter to select, 'q' to quit)\n")
        
        BLUE = "\033[94m"
        NC = "\033[0m"  # No Color

        for i, exercise in enumerate(self.exercises):
            if i == self.selected_index:
                print(f"{BLUE}❯ {exercise}{NC}")
            else:
                print(f"  {exercise}")
        
        print(f"\nShowing {len(self.exercises)} exercises")
    
    # def get_exercise_data(self, exercise):
    #     """Get processed data for a specific exercise"""
    #     data = self.df[self.df['Exercise'] == exercise].copy()
    #     data = data.sort_values('Workout Start')
        
    #     # Determine primary metric based on exercise data
    #     if data['Weight'].notna().any() and data['Weight'].max() > 0:
    #         metric = 'Weight'
    #     elif data['Duration'].notna().any() and data['Duration'].max() > 0:
    #         metric = 'Duration'
    #     elif data['Distance'].notna().any() and data['Distance'].max() > 0:
    #         metric = 'Distance'
    #     else:
    #         metric = 'Reps'
        
    #     # Group by date and get max value for each day
    #     daily_data = data.groupby(data['Workout Start'].dt.date).agg({
    #         metric: 'max',
    #         'Reps': 'max'
    #     }).reset_index()
        
    #     return daily_data, metric
    
    # def create_ascii_chart(self, dates, values, metric, exercise):
    #     """Create beautiful ASCII chart"""
    #     if len(values) < 2:
    #         return f"Not enough data points for {exercise}"
        
    #     # Chart dimensions
    #     width = min(80, len(values) * 2 + 10)
    #     height = 20
        
    #     # Normalize values to chart height
    #     min_val = min(values)
    #     max_val = max(values)
    #     val_range = max_val - min_val if max_val != min_val else 1
        
    #     # Create chart
    #     chart = []
    #     chart.append(f"📈 {exercise} - {metric} Progression")
    #     chart.append("=" * (len(exercise) + len(metric) + 20))
    #     chart.append("")
        
    #     # Y-axis labels and chart body
    #     for row in range(height, 0, -1):
    #         line = ""
    #         current_val = min_val + (val_range * row / height)
            
    #         # Y-axis label
    #         if row == height:
    #             line += f"{max_val:6.1f} ┤"
    #         elif row == 1:
    #             line += f"{min_val:6.1f} ┤"
    #         elif row == height // 2:
    #             line += f"{(max_val + min_val) / 2:6.1f} ┤"
    #         else:
    #             line += "       │"
            
    #         # Chart points
    #         for i, val in enumerate(values):
    #             normalized = (val - min_val) / val_range * height
    #             if abs(normalized - row) < 0.5:
    #                 line += "●"
    #             elif i > 0:
    #                 prev_val = values[i-1]
    #                 prev_normalized = (prev_val - min_val) / val_range * height
    #                 if min(normalized, prev_normalized) < row < max(normalized, prev_normalized):
    #                     line += "│"
    #                 else:
    #                     line += " "
    #             else:
    #                 line += " "
            
    #         chart.append(line)
        
    #     # X-axis
    #     chart.append("       └" + "─" * len(values))
        
    #     # Date labels (show first, last, and middle dates)
    #     if len(dates) > 1:
    #         date_line = "        "
    #         date_line += dates[0].strftime("%m/%d")
    #         if len(dates) > 2:
    #             mid_spaces = len(values) - len(dates[0].strftime("%m/%d")) - len(dates[-1].strftime("%m/%d"))
    #             date_line += " " * (mid_spaces // 2)
    #             if len(dates) > 3:
    #                 date_line += dates[len(dates)//2].strftime("%m/%d")
    #                 remaining_spaces = mid_spaces - mid_spaces // 2 - len(dates[len(dates)//2].strftime("%m/%d"))
    #                 date_line += " " * remaining_spaces
    #             else:
    #                 date_line += " " * mid_spaces
    #         date_line += dates[-1].strftime("%m/%d")
    #         chart.append(date_line)
        
    #     # Statistics
    #     chart.append("")
    #     chart.append(f"📊 Stats: Min: {min_val:.1f} | Max: {max_val:.1f} | Latest: {values[-1]:.1f}")
    #     chart.append(f"📅 Period: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
    #     chart.append(f"📈 Total Sessions: {len(values)}")

    #     if len(values) > 1:
    #         improvement = values[-1] - values[0]
    #         improvement_pct = (improvement / values[0]) * 100 if values[0] != 0 else 0
    #         chart.append(f"🚀 Progress: {improvement:+.1f} ({improvement_pct:+.1f}%)")
        
    #     return "\n".join(chart)
    
    # def show_exercise_chart(self, exercise):
    #     """Display chart for selected exercise"""
    #     self.clear_screen()
        
    #     try:
    #         daily_data, metric = self.get_exercise_data(exercise)
            
    #         if daily_data.empty:
    #             print(f"No data found for {exercise}")
    #             input("\nPress Enter to continue...")
    #             return
            
    #         dates = pd.to_datetime(daily_data['Workout Start']).dt.date
    #         values = daily_data[metric].values
            
    #         chart = self.create_ascii_chart(dates, values, metric, exercise)
    #         print(chart)
            
    #     except Exception as e:
    #         print(f"Error creating chart: {e}")
        
    #     print("\nPress Enter to return to menu...")
    #     input()
    
    def run(self):
        """Main application loop"""
        while True:
            self.display_menu()
            
            key = self.get_key()
            
            if key == 'q':
                print("\nGoodbye! 💪")
                break
            elif key == '\x1b[A':  # Up arrow
                self.selected_index = (self.selected_index - 1) % len(self.exercises)
            elif key == '\x1b[B':  # Down arrow
                self.selected_index = (self.selected_index + 1) % len(self.exercises)
            elif key == '\r' or key == '\n':  # Enter
                selected_exercise = self.exercises[self.selected_index]
                self.show_exercise_chart(selected_exercise)

def main():
    if len(sys.argv) != 2:
        print("Usage: python workout_visualizer.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"Error: File '{csv_file}' not found")
        sys.exit(1)
    
    try:
        visualizer = WorkoutVisualizer(csv_file)
        visualizer.run()
    except KeyboardInterrupt:
        print("\nExiting... 💪")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
