import requests
from pandas import json_normalize
import tkinter as tk
from tkinter import ttk
import numpy as np
import random

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
                                pass

    return english_name, description, master_threshold

def format_array(df, s_server):
    result = np.empty((0, 6), str)  # Initialize an empty numpy array to store the results

    for index, row in df.iterrows():
        challenge_id = row['challengeId']
        level = row['level']
        value = row['value']
        english_name, description, master_threshold = get_challenge_data(challenge_id, s_server)
        done_or_not = max(0 , int(master_threshold-value))
        if done_or_not == 0 : done_or_not = "DONE"
        result = np.append(result, np.array([[english_name, description, level, int(value), done_or_not, int(master_threshold)]]), axis=0)
    
    return result

def format_array_update(df, old_arr, s_server):
    arr = format_array(df, s_server)
    for i in range(len(arr)):
        if arr[i][4] != old_arr[i][4]:
            if arr[i][4] != "DONE":
                arr[i][4] = f"{arr[i][4]} + ({int(old_arr[i][4]) - int(arr[i][4])})"
    return arr

def data_window():
    # create a new window
    root = tk.Tk()
    root.title("Enter Summoner Name")

    # create a text box and a button for entering the summoner name
    label = tk.Label(root, text="Enter Summoner Name:")
    label.pack(padx=5, pady=5)

    entry = tk.Entry(root)
    entry.pack(side=tk.LEFT, padx=5, pady=5)

    # create a list of possible values for the dropdown menu
    values = ["EUW", "EUNE", "NA", "OCE", "KR", "LAN", "LAS"]
    arg_values = ["euw1", "eun1", "na1", "oc1", "kr", "la1", "la2"]

    # create the dropdown menu and add it to the window
    var = tk.StringVar(root)
    var.set(values[0])
    dropdown = tk.OptionMenu(root, var, *values)
    dropdown.config(width=len("EUW") + 1)
    dropdown.pack(side=tk.LEFT)

    button = tk.Button(root, text="OK", command=lambda: user_exists(entry.get(), arg_values[values.index(var.get())], root))
    button.pack(side=tk.LEFT, padx=5, pady=5)

    # run the main loop to display the window
    root.mainloop()

def user_exists(s_name, s_server, root):
    try:
        get_puuid(s_name, s_server)
        launch_app(s_name, s_server, root)
    except Exception as e:
        random_num = random.random()
        label_exists = False
        for child in root.winfo_children():
            if isinstance(child, tk.Label) and (child.cget("text") == "Summoner does not exist" or child.cget("text") == "SuMonn3r dOeS n0t ExIsT"):
                label_exists = True
                break

        if not label_exists:
            if random_num < 0.1:
                string_label = tk.Label(root, text="SuMonn3r dOeS n0t ExIsT")
                string_label.pack(side=tk.LEFT, padx=5, pady=5)
    
            else:
                string_label = tk.Label(root, text="Summoner does not exist")
                string_label.pack(side=tk.LEFT, padx=5, pady=5)

def refresh(s_name, old_arr, s_server, s_progress, root):
    # Setup
    s_puuid = get_puuid(s_name, s_server)
    s_challenges = get_challenges(s_puuid, s_server)
    arr = format_array_update(s_challenges, old_arr, s_server)
    s_progress  = get_progress(format_array(s_challenges, s_server))

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
    
    refresh_button = tk.Button(root, text="Refresh Data", command=lambda: refresh(s_name, format_array(s_challenges, s_server), s_server, 10, root))
    refresh_button.pack(pady=10)

    root.mainloop()
    root.update()

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
    
    refresh_button = tk.Button(root, text="Refresh Data", command=lambda: refresh(s_name, arr, s_server, 10, root))
    refresh_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__" :
    data_window()
    # data_window -> user_exists -> launch_app -> get_puuid, get_challenges, get_progress, format_array -> refresh