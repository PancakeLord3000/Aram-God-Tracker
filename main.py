import requests
from pandas import json_normalize
import tkinter as tk
from tkinter import ttk
import numpy as np
import random
import concurrent.futures
import time

API_KEY = "..." # here's where you add your riot api key

def get_challenges(puuid, s_server):
    url = f"https://{s_server}.api.riotgames.com/lol/challenges/v1/player-data/" + puuid + "?api_key=" + API_KEY

    response = requests.get(url)

    # Get the JSON data from the response
    data = response.json()
    
    # Print the JSON data in a legible format
    data = data["challenges"]
    df = json_normalize(data)
    
    # Filter
    df["challengeId_str"] = df["challengeId"].apply(lambda x: str(x)[:3])
    #Take sub-sections
    df = df[df["challengeId_str"] == "101"]

    return df

def get_puuid(summoner_name, s_server):
    url = f"https://{s_server}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}" + "?api_key=" + API_KEY
    response = requests.get(url)
    # Get the JSON data from the response
    data = response.json()
    df = json_normalize(data)
    return df["puuid"].iloc[0]

def float_to_ints(arr):
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            try:
                arr[i, j] = int(arr[i, j])
            except ValueError:
                pass
    return arr

def get_progress(arr):
    avrg = []
    for row in arr:
        if row[0] != "ARAM Authority":
            tmp = int(row[3])/int(row[5])
            if tmp > 1:
               avrg.append(1)
            else: 
                avrg.append(tmp)
    return calculate_average(avrg) * 100

def calculate_average(float_array):
    total = 0
    count = 0
    for number in float_array:
        total += number
        count += 1
    average = total / count
    return average

def get_challenge_data(id, s_server):
    url = f"https://{s_server}.api.riotgames.com/lol/challenges/v1/challenges/{id}/config" + "?api_key=" + API_KEY
    response = requests.get(url)
    response_json = response.json()

    # Extract the relevant information from the JSON
    english_name = response_json['localizedNames']['en_GB']['name']
    description = response_json['localizedNames']['en_GB']['description']
    try:
        master_threshold = response_json['thresholds']['MASTER']
    except:
        try:
            master_threshold = response_json['thresholds']['DIAMOND']
        except:
            try:
                master_threshold = response_json['thresholds']['PLATINUM']
            except:
                try:
                    master_threshold = response_json['thresholds']['GOLD']
                except:
                    try:
                        master_threshold = response_json['thresholds']['SILVER']
                    except:
                        try:
                            master_threshold = response_json['thresholds']['BRONZE']
                        except:
                            try:
                                master_threshold = response_json['thresholds']['IRON']
                            except:
                                master_threshold = ""

    return english_name, description, master_threshold

def format_array(df, s_server):
    result = np.empty((0, 6), str)  # Initialize an empty numpy array to store the results with fixed shape

    # Define a helper function to call get_challenge_data for a single row
    def get_challenge_data_for_row(row):
        challenge_id = row.challengeId
        level = row.level
        value = row.value
        # if you just call time.sleep(n) then all the calls to get_challenge_data_for_row will wait n seconds and then execute at the same time
        wait_time = random.uniform(0.5, 2) # generates a random float between 0.5 and 2
        time.sleep(wait_time) # then wait it
        english_name, description, master_threshold = get_challenge_data(challenge_id, s_server)
        done_or_not = max(0, int(master_threshold - value))
        if done_or_not == 0:
            done_or_not = "DONE"
        return [english_name, description, level, int(value), done_or_not, int(master_threshold)]

    # Use ThreadPoolExecutor to asynchronously call get_challenge_data for each row
    result = []
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(get_challenge_data_for_row, df.itertuples(index=False)))
    except Exception as e:
        print("An exception of type {0} occurred: {1}\nTrying again...".format(type(e).__name__, str(e)))
        time.sleep(2) # just in case that we exceeded the api calls per second but not the api calls per minute
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = list(executor.map(get_challenge_data_for_row, df.itertuples(index=False)))

    # Convert the list of results to a numpy array
    result = np.array(results)

    return result

def format_array_update(df, old_arr, s_server):
    arr = format_array(df, s_server)
    former_add = arr.copy()
    for i in range(len(arr)):
        if arr[i][4] != old_arr[i][4]:
            if arr[i][4] != "DONE":
                arr[i][4] = f"{arr[i][4]} + ({int(old_arr[i][4]) - int(arr[i][4])})"
    return arr, former_add

def add_summoner_name(summoner_name):
    # check if summoner name already exists in file
    with open('summoner_names.txt', 'r') as file:
        if summoner_name in file.read():
            return

    # append summoner name to file
    with open('summoner_names.txt', 'a') as file:
        file.write(summoner_name + '\n')

class AutocompleteEntry(tk.Entry):
    def __init__(self, master, options, width=30, font=("Arial", 14), **kw):
        super().__init__(master, width=width, font=font, **kw)

        self.options = options

        # create a listbox to display suggestions
        self.listbox = tk.Listbox(master, width=30)
        self.listbox.bind("<Button-1>", self.on_select)

        # bind events to update the listbox
        self.bind("<KeyRelease>", self.on_key_release)
        self.bind("<Up>", self.on_up)
        self.bind("<Down>", self.on_down)

    def on_key_release(self, event):
        # clear the listbox and reset the options
        self.listbox.delete(0, tk.END)
        self.matches = []
        text = self.get()

        # get matches for the current text
        for option in self.options:
            if text.lower() in option.lower():
                self.matches.append(option)

        # update the listbox with matches
        for match in self.matches:
            self.listbox.insert(tk.END, match)

        if self.matches:
            self.listbox.place(x=self.winfo_x(), y=self.winfo_y() + self.winfo_height())
        else:
            self.listbox.place_forget()

    def on_up(self, event):
        if self.listbox.curselection() == ():
            index = 'end'
        else:
            index = self.listbox.curselection()[0]
        if index == '0':
            self.listbox.selection_clear(0, 'end')
            self.icursor('end')
            return
        self.listbox.selection_clear(0, 'end')
        self.listbox.activate(int(index) - 1)
        self.listbox.selection_set(int(index) - 1, 'end')
        self.icursor('end')

    def on_down(self, event):
        if self.listbox.curselection() == ():
            index = '-1'
        else:
            index = self.listbox.curselection()[0]
        if index == tk.END:
            self.listbox.selection_clear(0, 'end')
            self.icursor('end')
            return
        self.listbox.selection_clear(0, 'end')
        self.listbox.activate(int(index) + 1)
        self.listbox.selection_set(int(index) + 1, 'end')
        self.icursor('end')

    def on_select(self, event):
        selected = self.listbox.get(self.listbox.curselection())
        self.delete(0, tk.END)
        self.insert(tk.END, selected)
        self.listbox.place_forget()

def data_window():
    # Create a new tkinter window
    window = tk.Tk()
    window.geometry("600x225")
    window.title("Aram God Tracker")

    # Create a label
    label = tk.Label(window, text="Enter Summoner Name", font=("Arial", 16))
    label.pack(pady=10)

    # Create a frame to hold the text entry, dropdown menu, and button
    frame = tk.Frame(window)
    frame.pack(fill=tk.BOTH, expand=True, pady=10)

    # read summoner names from the file
    with open("summoner_names.txt", "r") as f:
        summoner_names = [line.strip() for line in f.readlines()]

    # Create the text entry
    entry = AutocompleteEntry(master=frame, options=summoner_names)
    entry.pack(side=tk.LEFT, padx=10)
    tk.Entry()
    
    # create a list of possible values for the dropdown menu
    values = ["EUW", "EUNE", "NA", "OCE", "KR", "LAN", "LAS"]
    arg_values = ["euw1", "eun1", "na1", "oc1", "kr", "la1", "la2"]

    # Create the dropdown menu
    dropdown_var = tk.StringVar(window)
    dropdown_var.set(values[0])
    dropdown = tk.OptionMenu(frame, dropdown_var, *values)
    dropdown.config(width=len("EUW")+1, font=("Arial", 14))
    dropdown.pack(side=tk.LEFT, padx=10)

    # Create the OK button
    ok_button = tk.Button(frame, text="Search", font=("Arial", 14), command=lambda: user_exists(entry.get(), arg_values[values.index(dropdown_var.get())], window))
    ok_button.pack(side=tk.RIGHT, padx=10)

    # Start the tkinter event loop
    window.mainloop()

def user_exists(s_name, s_server, root):
    if not len(s_name) > 0 : 
        label_exists = False
        for child in root.winfo_children():
            if isinstance(child, tk.Label) and child.cget("text") == "Incorrect name format":
                label_exists = True
                break

        if not label_exists:
            string_label = tk.Label(root, text="Incorrect name format")
            string_label.pack(pady=10)

        return 0
    
    try:
        get_puuid(s_name, s_server)
        add_summoner_name((s_name))
        launch_app(s_name, s_server, root)
    except Exception as e:
        # Basic error handling to user ui
        print("An exception of type {0} occurred: {1}".format(type(e).__name__, str(e)))
        if str(type(e).__name__) == "KeyError":
            label_exists = False
            for child in root.winfo_children():
                if isinstance(child, tk.Label) and child.cget("text") == "Please wait a while before using the app again":
                    label_exists = True
                    break

            if not label_exists:
                string_label = tk.Label(root, text="Please wait a while before using the app again")
                string_label.pack(pady=10)
        else:
            random_num = random.random()
            label_exists = False
            for child in root.winfo_children():
                if isinstance(child, tk.Label) and (child.cget("text") == "Summoner does not exist" or child.cget("text") == "SuMonn3r dOeS n0t ExIsT!"):
                    label_exists = True
                    break

            if not label_exists:
                if random_num < 0.1:
                    string_label = tk.Label(root, text="SuMonn3r dOeS n0t ExIsT!")
                    string_label.pack(pady=10)
        
                else:
                    string_label = tk.Label(root, text="Summoner does not exist")
                    string_label.pack(pady=10)
    return 0

def refresh(s_name, old_arr, s_server, s_progress, root, first = False):
    # Setup
    s_puuid = get_puuid(s_name, s_server)
    s_challenges = get_challenges(s_puuid, s_server)
    if first :
        arr = former_arr = old_arr
    else:
        arr, former_arr = format_array_update(s_challenges, old_arr, s_server)
    s_progress  = get_progress(former_arr)

    for widget in root.winfo_children():
        widget.destroy()

    # Create a grid layout
    grid = tk.Frame(root)
    grid.pack(padx=5, pady=5)
    root.update()
    
    # Add column names to the grid
    column_names = ["CHALLENGE NAME", "DESCRIPTION", "CURRENT RANK", "CURRENT POINTS", "POINTS TO MASTER", "MASTER POINTS"]
    for i, name in enumerate(column_names):
        tk.Label(grid, text=name, font=("Verdana", 12, "bold"), justify="left").grid(row=0, column=i)
    root.update()
    
    # Add array elements to the grid
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            tk.Label(grid, text=arr[i, j], justify="left").grid(row=i+1, column=j)
    root.update()
    
    # Progress bar
    progress = tk.DoubleVar()  # Create a DoubleVar to hold the progress value
    progress_bar = ttk.Progressbar(root, variable=progress, maximum=100, mode='determinate', length=int(root.winfo_width() * 0.8))
    progress_bar.pack(pady=10)  # Add progress bar to the GUI, with some padding below it
    # Add label to display progress percentage in the center of the progress bar
    progress_label = tk.Label(progress_bar, text='', font=("Verdana", 10))
    progress_label.place(relx=0.5, rely=0.5, anchor="center")
    progress.set(s_progress)  # Update progress bar with new value
    progress_label.configure(text=f"{int(s_progress)}%")  # Update progress label with new value
    root.update()
    
    # Refresh button
    def disable_refresh_button():
        refresh_button.configure(state='disabled')
        countdown_seconds = 60
        def update_countdown():
            nonlocal countdown_seconds
            countdown_seconds -= 1
            if countdown_seconds > 0:
                refresh_button.configure(text=f"Wait {countdown_seconds} sec")
                root.after(1000, update_countdown)
            else:
                refresh_button.configure(text="Refresh Data", state='normal')
        update_countdown()

    def enable_refresh_button():
        refresh_button.configure(state='normal', text="Refresh Data")

    def refresh_b():
        refresh(s_name, format_array(s_challenges, s_server), s_server, s_progress, root)
    
    refresh_button = tk.Button(root, text="Refresh Data", command=refresh_b)
    refresh_button.pack(pady=10)
    disable_refresh_button()
    root.after(60000, enable_refresh_button)
    root.update()

    root.mainloop()

def launch_app(s_name, s_server, root_old):
    # Setup
    s_puuid = get_puuid(s_name, s_server)
    s_challenges = get_challenges(s_puuid, s_server)
    arr = format_array(s_challenges, s_server)
    s_progress  = get_progress(arr)

    # create a new window
    root_old.destroy()
    root = tk.Tk()
    root.geometry("1400x625+100+100")  
    root.title(s_name)

    refresh(s_name, arr, s_server, s_progress, root, first = True)

    root.mainloop()

if __name__ == "__main__" :
    data_window()
    # data_window -> user_exists -> launch_app -> get_puuid, get_challenges, get_progress, format_array -> refresh