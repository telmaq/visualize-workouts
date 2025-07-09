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

class WorkoutMenuUI:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.exercises = data_loader.get_exercises()

    def plot_weight_over_time_plotext(self, dates, weights, label='Weight over time'):
        if not weights or len(weights) < 2:
            print('Not enough data to plot.')
            return
        plt.clear_figure()
        plt.title(label)
        plt.xlabel('Date')
        plt.ylabel('Weight')
        plt.plot(dates, weights, marker='dot', color='green+')
        plt.canvas_color('black')
        plt.axes_color('black')
        plt.ticks_color('white')
        # plt.xticks(rotation=15, automatic=True)
        # plt.tight_layout()
        plt.show()

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

            for i, exercise in enumerate(filtered_exercises[scroll_offset:scroll_offset + num_display_lines]):
                row = 7 + i
                is_selected = (i + scroll_offset == selected_index)
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
                    stdscr.addstr(4, 0, "(See terminal for plot)")
                    stdscr.refresh()
                    curses.endwin()  # End curses mode before printing
                    # Prepare data, drop missing weights and align dates
                    weights = list(exercise_data['Weight'].dropna())
                    dates = list(exercise_data.loc[exercise_data['Weight'].notna(), 'Workout Start'].dt.strftime('%d/%m/%Y'))
                    self.plot_weight_over_time_plotext(dates, weights, label=f'Weight over time: {exercise_name}')
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
