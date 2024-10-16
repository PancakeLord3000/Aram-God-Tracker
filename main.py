import json
import os
import tkinter as tk
from tkinter import ttk
import requests
import numpy as np
from tkinter import messagebox
from pandas import json_normalize
import concurrent.futures
import time
import random

API_KEY = "..." # here's where you add your riot api key

def get_puuid(game_name, tag_line):
    url = f"https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}?api_key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data["puuid"]

def get_challenges(puuid):
    url = f"https://euw1.api.riotgames.com/lol/challenges/v1/player-data/{puuid}?api_key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    df = json_normalize(data["challenges"])
    df = df[df["challengeId"].astype(str).str[:3] == "101"]
    return df

def get_challenge_data(id):
    url = f"https://euw1.api.riotgames.com/lol/challenges/v1/challenges/{id}/config?api_key={API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    english_name = data['localizedNames']['en_GB']['name']
    description = data['localizedNames']['en_GB']['description']
    thresholds = ['MASTER', 'DIAMOND', 'PLATINUM', 'GOLD', 'SILVER', 'BRONZE', 'IRON']
    
    for threshold in thresholds:
        if threshold in data['thresholds']:
            master_threshold = data['thresholds'][threshold]
            break
    else:
        master_threshold = ""

    return english_name, description, master_threshold

def format_array(df):
    def get_challenge_data_for_row(row):
        challenge_id = row.challengeId
        level = row.level
        value = row.value
        wait_time = random.uniform(0.5, 2)
        time.sleep(wait_time)
        english_name, description, master_threshold = get_challenge_data(challenge_id)
        done_or_not = max(0, int(master_threshold) - int(value))
        if done_or_not == 0:
            done_or_not = "DONE"
        return [english_name, description, level, int(value), done_or_not, int(master_threshold)]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(get_challenge_data_for_row, df.itertuples(index=False)))

    return np.array(results)

def get_progress(arr):
    return float(arr[0][3]) / float(arr[0][5]) * 100

class ChallengeTrackerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("LoL Challenge Tracker")
        self.master.geometry("1000x650")

        self.create_widgets()
        self.load_previous_searches()

    def create_widgets(self):
        self.frame = ttk.Frame(self.master, padding="10")
        self.frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        ttk.Label(self.frame, text="Summoner Name:").grid(column=0, row=0, sticky=tk.W)
        self.summoner_name = tk.StringVar()
        self.summoner_entry = ttk.Combobox(self.frame, width=30, textvariable=self.summoner_name)
        self.summoner_entry.grid(column=1, row=0, sticky=(tk.W, tk.E))

        ttk.Label(self.frame, text="Tag Line:").grid(column=0, row=1, sticky=tk.W)
        self.tag_line = tk.StringVar()
        self.tag_entry = ttk.Combobox(self.frame, width=30, textvariable=self.tag_line)
        self.tag_entry.grid(column=1, row=1, sticky=(tk.W, tk.E))

        self.search_button = ttk.Button(self.frame, text="Search", command=self.search_summoner)
        self.search_button.grid(column=2, row=0, rowspan=2)
        
        self.result_tree = ttk.Treeview(self.frame, columns=("name", "description", "rank", "points", "to_master"), show="headings")
        self.result_tree.grid(column=0, row=2, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=1)

        # Set column widths
        self.result_tree.column("name", width=175, minwidth=168)
        self.result_tree.column("description", width=530, minwidth=0)
        self.result_tree.column("rank", width=92, minwidth=92)
        self.result_tree.column("points", width=90, minwidth=100)
        self.result_tree.column("to_master", width=100, minwidth=100)

        # Set column headings
        self.result_tree.heading("name", text="Name")
        self.result_tree.heading("description", text="Description")
        self.result_tree.heading("rank", text="Rank")
        self.result_tree.heading("points", text="Points")
        self.result_tree.heading("to_master", text="Points to Master")

        self.result_tree.tag_configure('oddrow', background='#f0f0f0')

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame, length=200, mode="determinate", variable=self.progress_var)
        self.progress_bar.grid(column=0, row=3, columnspan=3, sticky=(tk.W, tk.E))
        
        self.progress_label = ttk.Label(self.frame, text="0%", anchor="center")
        self.progress_label.grid(column=0, row=3, columnspan=3)

        self.refresh_button = ttk.Button(self.frame, text="Refresh Data", command=self.refresh_data, state="disabled")
        self.refresh_button.grid(column=0, row=4, columnspan=3)

    def load_previous_searches(self):
        if os.path.exists('previous_searches.json'):
            with open('previous_searches.json', 'r') as f:
                previous_searches = json.load(f)
                self.summoner_entry['values'] = previous_searches.get('summoner_names', [])
                self.tag_entry['values'] = previous_searches.get('tag_lines', [])

    def save_search(self, summoner_name, tag_line):
        previous_searches = {}
        if os.path.exists('previous_searches.json'):
            with open('previous_searches.json', 'r') as f:
                previous_searches = json.load(f)

        summoner_names = previous_searches.get('summoner_names', [])
        tag_lines = previous_searches.get('tag_lines', [])

        if summoner_name not in summoner_names:
            summoner_names.append(summoner_name)
        if tag_line not in tag_lines:
            tag_lines.append(tag_line)

        previous_searches['summoner_names'] = summoner_names[-10:]  # Keep only the last 10
        previous_searches['tag_lines'] = tag_lines[-10:]  # Keep only the last 10

        with open('previous_searches.json', 'w') as f:
            json.dump(previous_searches, f)

        self.summoner_entry['values'] = previous_searches['summoner_names']
        self.tag_entry['values'] = previous_searches['tag_lines']

    def search_summoner(self):
        game_name = self.summoner_name.get()
        tag_line = self.tag_line.get()

        try:
            puuid = get_puuid(game_name, tag_line)
            challenges_df = get_challenges(puuid)
            self.challenges_array = format_array(challenges_df)
            self.update_display()
            self.refresh_button["state"] = "normal"
            self.save_search(game_name, tag_line)
        except Exception as e:
            tk.messagebox.showerror("Can't find summoner", f"Verify the information or try again later")
            
    def update_display(self):
        self.result_tree.delete(*self.result_tree.get_children())
        for i, row in enumerate(self.challenges_array):
            tags = ('oddrow',) if i % 2 else ()
            self.result_tree.insert("", "end", values=tuple(row), tags=tags)

        progress = get_progress(self.challenges_array)
        self.progress_var.set(progress)
        self.progress_label.config(text=f"{progress:.1f}%")

    def refresh_data(self):
        self.refresh_button["state"] = "disabled"
        self.master.after(60000, lambda: self.refresh_button.config(state="normal"))
        self.search_summoner()

def main():
    root = tk.Tk()
    app = ChallengeTrackerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()