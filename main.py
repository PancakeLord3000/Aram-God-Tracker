import tkinter
import requests
from pandas import json_normalize
import tkinter as tk
import numpy as np

API_KEY = "..."

def get_challenges(puuid):
    url = "https://euw1.api.riotgames.com/lol/challenges/v1/player-data/" + puuid + "?api_key=" + API_KEY

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

def get_challenge_data(id):
    url = f"https://euw1.api.riotgames.com/lol/challenges/v1/challenges/{id}/config" + "?api_key=" + API_KEY

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

def format_array(df):
    result = np.empty((0, 6), str)  # Initialize an empty numpy array to store the results

    for index, row in df.iterrows():
        challenge_id = row['challengeId']
        level = row['level']
        value = row['value']
        english_name, description, master_threshold = get_challenge_data(challenge_id)
        done_or_not = max(0 , int(master_threshold-value))
        if done_or_not == 0 : done_or_not = "DONE"
        result = np.append(result, np.array([[english_name, description, level, int(value), done_or_not, int(master_threshold)]]), axis=0)
    
    return result

def format_array_update(df, old_arr):
    arr = format_array(df)
    for i in range(len(arr)):
        if arr[i][4] != old_arr[i][4]:
            if arr[i][4] != "DONE":
                arr[i][4] = f"{arr[i][4]} + ({int(old_arr[i][4]) - int(arr[i][4])})"
    return arr

def get_puuid(summoner_name):
    url = f"https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}" + "?api_key=" + API_KEY
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

def refresh(s_name, old_arr, root):
    # Setup
    s_puuid = get_puuid(s_name)
    s_challenges = get_challenges(s_puuid)
    arr = format_array_update(s_challenges, old_arr)

    for widget in root.winfo_children():
        widget.destroy()

    # Create a grid layout
    grid = tkinter.Frame(root)
    grid.pack(padx=5, pady=5)


    # Add column names to the grid
    column_names = ["CHALLENGE NAME", "DESCRIPTION", "CURRENT RANK", "CURRENT POINTS", "POINTS TO MASTER", "MASTER POINTS"]
    for i, name in enumerate(column_names):
        tk.Label(grid, text=name, font=("Verdana", 12, "bold"), justify="left").grid(row=0, column=i)

    # Add array elements to the grid
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            tk.Label(grid, text=arr[i, j]).grid(row=i+1, column=j)

    refresh_button = tk.Button(root, text="Refresh Data", command=lambda: refresh(s_name, arr, root))
    refresh_button.pack()

    root.update()

def data_window():
    # create a new window
    root = tkinter.Tk()
    root.title("Enter Summoner Name")

    # create a text box and a button for entering the summoner name
    label = tkinter.Label(root, text="Enter Summoner Name:")
    label.pack(padx=5, pady=5)

    entry = tkinter.Entry(root)
    entry.pack(padx=5, pady=5)

    button = tkinter.Button(root, text="OK", command=lambda: launch_app(entry.get(), root))
    button.pack(padx=5, pady=5)

    root.mainloop()

def launch_app(s_name, root):
    # Setup
    s_puuid = get_puuid(s_name)
    s_challenges = get_challenges(s_puuid)
    arr = format_array(s_challenges)

    # create a new window
    root.destroy()
    root = tkinter.Tk()
    root.title(s_name)

    # Create a grid layout
    grid = tkinter.Frame(root)
    grid.pack(padx=5, pady=5)

    # Add column names to the grid
    column_names = ["CHALLENGE NAME", "DESCRIPTION", "CURRENT RANK", "CURRENT POINTS", "POINTS TO MASTER", "MASTER POINTS"]
    for i, name in enumerate(column_names):
        tk.Label(grid, text=name, font=("Verdana", 12, "bold"), justify="left").grid(row=0, column=i)

    # Add array elements to the grid
    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            tk.Label(grid, text=arr[i, j]).grid(row=i+1, column=j)

    refresh_button = tk.Button(root, text="Refresh Data", command=lambda: refresh(s_name, arr, root))
    refresh_button.pack()

    root.mainloop()

if __name__ == "__main__" :
    data_window()
