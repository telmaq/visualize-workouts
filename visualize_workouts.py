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
    
    def display_menu_curses(self, stdscr):
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
            stdscr.addstr(4, 0, "(↑/↓: navigate, Enter: select, q: quit, type to search)")
            stdscr.addstr(5, 0, f"Search: {search_query}")

            # Filter exercises based on search query
            filtered_exercises = [ex for ex in self.exercises if search_query.lower() in ex.lower()]
            num_display_lines = max_y - 7  # 6 header lines + 1 for prompt

            # Adjust selected_index if out of bounds
            if selected_index >= len(filtered_exercises):
                selected_index = max(0, len(filtered_exercises) - 1)

            # Scrolling logic
            if selected_index < scroll_offset:
                scroll_offset = selected_index
            elif selected_index >= scroll_offset + num_display_lines:
                scroll_offset = selected_index - num_display_lines + 1

            for i, exercise in enumerate(filtered_exercises[scroll_offset:scroll_offset + num_display_lines]):
                row = 7 + i
                if i + scroll_offset == selected_index:
                    stdscr.attron(curses.color_pair(1))
                    stdscr.addstr(row, 0, f"❯ {exercise}")
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.addstr(row, 0, f"  {exercise}")

            stdscr.refresh()
            key = stdscr.getch()

            if key == ord('q'):
                break
            elif key == curses.KEY_UP:
                if selected_index > 0:
                    selected_index -= 1
            elif key == curses.KEY_DOWN:
                if selected_index < len(filtered_exercises) - 1:
                    selected_index += 1
            elif key in [curses.KEY_ENTER, 10, 13]:
                if filtered_exercises:
                    stdscr.clear()
                    stdscr.addstr(0, 0, f"You selected: {filtered_exercises[selected_index]}")
                    stdscr.addstr(2, 0, "Press any key to return to menu...")
                    stdscr.refresh()
                    stdscr.getch()
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                search_query = search_query[:-1]
                selected_index = 0
                scroll_offset = 0
            elif key == 27:  # ESC clears search
                search_query = ""
                selected_index = 0
                scroll_offset = 0
            elif 32 <= key <= 126:  # Printable characters
                search_query += chr(key)
                selected_index = 0
                scroll_offset = 0

    def run(self):
        curses.wrapper(self.curses_main)

    def curses_main(self, stdscr):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        self.display_menu_curses(stdscr)

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
