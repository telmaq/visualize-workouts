#!/usr/bin/env python3

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import termios
import tty
import os
from collections import defaultdict
import curses
import plotext as plt
from asciichartpy import plot

class WorkoutDataLoader:
    def __init__(self, csv_file):
        self.df = pd.read_csv(csv_file)
        self.df['Workout Start'] = pd.to_datetime(self.df['Workout Start'])
        self.exercises = sorted(self.df['Exercise'].dropna().unique())

    def get_exercises(self):
        return self.exercises

    def get_exercise_data(self, exercise):
        data = self.df[self.df['Exercise'] == exercise].copy()
        data = data.sort_values('Workout Start')
        return data


class WorkoutExerciseUI:
    def __init__(self, exercise, exercise_data):
        self.exercise = exercise
        self.exercise_data = exercise_data
        # Filter out rows with missing weight data and sort by date
        valid_data = exercise_data.dropna(subset=['Weight']).sort_values('Workout Start')
        # Remove duplicates by keeping the latest weight for each date
        self.dates = list(valid_data['Workout Start'])
        self.values = list(valid_data['Weight'])

    def create_ascii_chart(self, dates, values, metric, exercise_name):
        chart_output = plot(values, {'height': 15, 'format': '{:8.1f}'})
        return f"📈 {exercise_name} - {metric} Progression\n{chart_output}"



class WorkoutMenuUI:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.exercises = data_loader.get_exercises()

    def sparkline(self, values, width=30):
        """Create a Unicode sparkline from a list of values"""
        if not values:
            return " " * width

        min_val, max_val = min(values), max(values)
        if max_val == min_val:
            return " " * width

        # Map to sparkline characters (8 levels)
        spark_chars = " ▂▃▄▅▆▇█"
        normalized = [(v - min_val) / (max_val - min_val) * (len(spark_chars) - 1) for v in values]

        # Sample to fit width
        if len(normalized) > width:
            step = len(normalized) / width
            normalized = [normalized[int(i * step)] for i in range(width)]

        return ''.join(spark_chars[int(v)] for v in normalized)

    def display_menu(self, stdscr):
        curses.curs_set(0)
        max_y, max_x = stdscr.getmaxyx()
        search_query = ""
        filtered_exercises = self.exercises
        selected_index = 0
        scroll_offset = 0

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "🏋️  WORKOUT PROGRESSION VISUALIZER 🏋️")
            stdscr.addstr(1, 0, "=" * 50)
            stdscr.addstr(3, 0, "Select an exercise to visualize:")
            stdscr.addstr(4, 0, "(↑/↓: navigate, Enter: select, ctrl+c: quit, type to search)")
            stdscr.addstr(5, 0, f"Search (esc to clear): {search_query}")

            filtered_exercises = [ex for ex in self.exercises if search_query.lower() in ex.lower()]
            num_display_lines = max_y - 7
            if selected_index >= len(filtered_exercises):
                selected_index = max(0, len(filtered_exercises) - 1)

            if selected_index < scroll_offset:
                scroll_offset = selected_index
            elif selected_index >= scroll_offset + num_display_lines:
                scroll_offset = selected_index - num_display_lines + 1

            # Calculate the maximum exercise name length for right-aligned sparklines
            max_exercise_length = max(len(ex) for ex in filtered_exercises) if filtered_exercises else 0
            sparkline_start_col = max_exercise_length + 4  # 2 for arrow/space + 2 for padding
            sparkline_width = 16

            for i, exercise in enumerate(filtered_exercises[scroll_offset:scroll_offset + num_display_lines]):
                row = 7 + i
                is_selected = (i + scroll_offset == selected_index)
                # Generate sparkline for this exercise
                exercise_data = self.data_loader.get_exercise_data(exercise)
                weights = list(exercise_data['Weight'].dropna())
                spark = self.sparkline(weights, width=sparkline_width) if weights else ' ' * sparkline_width
                if search_query:
                    lower_ex = exercise.lower()
                    lower_query = search_query.lower()
                    start_idx = lower_ex.find(lower_query)
                else:
                    start_idx = -1

                if is_selected:
                    stdscr.attron(curses.color_pair(1))
                stdscr.addstr(row, 0, "❯ " if is_selected else "  ")
                col = 2
                if start_idx != -1 and search_query:
                    stdscr.addstr(row, col, exercise[:start_idx])
                    col += len(exercise[:start_idx])
                    stdscr.attron(curses.color_pair(2))
                    stdscr.addstr(row, col, exercise[start_idx:start_idx+len(search_query)])
                    stdscr.attroff(curses.color_pair(2))
                    col += len(search_query)
                    stdscr.addstr(row, col, exercise[start_idx+len(search_query):])
                else:
                    stdscr.addstr(row, col, exercise)

                # Right-align sparkline
                stdscr.addstr(row, sparkline_start_col, spark)
                if is_selected:
                    stdscr.attroff(curses.color_pair(1))

            stdscr.refresh()
            key = stdscr.getch()

            if key == curses.KEY_UP:
                if selected_index > 0:
                    selected_index -= 1
            elif key == curses.KEY_DOWN:
                if selected_index < len(filtered_exercises) - 1:
                    selected_index += 1
            elif key in [curses.KEY_ENTER, 10, 13]:

                if filtered_exercises:
                    stdscr.clear()
                    exercise_name = filtered_exercises[selected_index]
                    stdscr.addstr(0, 0, f"You selected: {exercise_name}")
                    stdscr.addstr(2, 0, "Press any key to return to menu...")
                    exercise_data = self.data_loader.get_exercise_data(exercise_name)
                    stdscr.addstr(4, 0, "(See terminal for sparkline)")
                    stdscr.refresh()
                    curses.endwin()  # End curses mode before printing
                    os.system('clear')  # Clear the terminal screen
                    # Prepare data, drop missing weights
                    weights = list(exercise_data['Weight'].dropna())
                    if weights:
                        workout_exercise = WorkoutExerciseUI(exercise_name, exercise_data)
                        workout_chart = workout_exercise.create_ascii_chart(workout_exercise.dates, workout_exercise.values, 'Weight', exercise_name)
                        print(workout_chart)
                        min_weight, max_weight = min(weights), max(weights)
                        # print(f"\nWeight over time: {exercise_name}")
                        # print(f"{spark}")
                        print(f"{min_weight:.1f} → {max_weight:.1f} lbs ({len(weights)} sessions)")
                    else:
                        print(f"\nNo weight data for: {exercise_name}")
                    input("Press Enter to return to menu...")
                    return  # Exit to menu after plot
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                search_query = search_query[:-1]
                selected_index = 0
                scroll_offset = 0
            elif key == 27:
                search_query = ""
                selected_index = 0
                scroll_offset = 0
            elif 32 <= key <= 126:
                search_query += chr(key)
                selected_index = 0
                scroll_offset = 0

class WorkoutVisualizer:
    def __init__(self, csv_file):
        self.data_loader = WorkoutDataLoader(csv_file)
        self.menu_ui = WorkoutMenuUI(self.data_loader)

    def run(self):
        curses.wrapper(self.curses_main)

    def curses_main(self, stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
        self.menu_ui.display_menu(stdscr)

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
