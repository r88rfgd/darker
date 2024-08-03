import time
import requests
from datetime import datetime
import traceback

# Constants
MC_DAY = 1200000
MC_MONTH = 37200000
MC_YEAR = 446400000  # Real-life milliseconds
SB_NEWYEAR = 1560275700000  # Skyblock Year 1 start in milliseconds
IRL_HOUR = 3600000
API_URL = "https://api.hypixel.net/v2/counts?key=5937f981-1c69-4c60-a53f-27c21bee5d1a"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1248098168059465768/bkHEvVQ-pYkpQPPeDsGl-B1E6RojSgoyyTY6Ge_mTS4nBHHFkTI_3uHM_nLG9pbd9htw"

def format_time(x):
    x = int(x / 1000)
    days = x // 86400
    hours = (x % 86400) // 3600
    minutes = (x % 3600) // 60
    seconds = x % 60
    return f'{days}d {hours:02}h {minutes:02}m {seconds:02}s'

def get_current_skyblock_time(curtime):
    sb_curtime = (curtime - SB_NEWYEAR) % MC_YEAR
    sb_cur_year = curtime - sb_curtime
    return sb_curtime, sb_cur_year

def dark_auction_timer():
    curtime = int(time.time() * 1000)
    sb_curtime, sb_cur_year = get_current_skyblock_time(curtime)
    start = sb_curtime - (sb_curtime % IRL_HOUR) + IRL_HOUR
    return sb_cur_year + start

def get_skyblock_data():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        data = response.json()
        return data['games']['SKYBLOCK']['modes']
    except requests.RequestException as e:
        error_message = f"Failed to fetch data from Hypixel API: {e}"
        print(error_message)
        send_error_to_discord(error_message)
        return None

def send_to_discord(embed):
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=embed)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to send data to Discord webhook: {e}")

def send_error_to_discord(error_message):
    embed = {
        "embeds": [
            {
                "title": "Dark Auction Monitor Error",
                "color": 15158332,
                "description": error_message,
                "timestamp": str(datetime.utcnow())
            }
        ]
    }
    send_to_discord(embed)

def print_timer(end_time):
    while True:
        try:
            curtime = int(time.time() * 1000)
            time_left = end_time - curtime
            if time_left <= 0:
                print("The Dark Auction is starting now!")
                break
            print(f"Time left until the next Dark Auction: {format_time(time_left)}", end='\r')
            time.sleep(1)
        except Exception as e:
            error_message = f"Error in print_timer: {e}\n{traceback.format_exc()}"
            print(error_message)
            send_error_to_discord(error_message)

def monitor_dark_auction(start_time):
    try:
        skyblock_data = get_skyblock_data()
        if skyblock_data and 'dark_auction' in skyblock_data:
            start_players = skyblock_data['dark_auction']
            print(f"Dark Auction started with {start_players} players at {datetime.fromtimestamp(start_time / 1000)}")

            total_players = start_players
            count = 1
            peak_players = start_players
            end_players = start_players
            lowest_players = start_players if start_players > 2 else float('inf')

            while 'dark_auction' in skyblock_data:
                try:
                    time.sleep(2)
                    skyblock_data = get_skyblock_data()
                    if skyblock_data and 'dark_auction' in skyblock_data:
                        current_players = skyblock_data['dark_auction']
                        total_players += current_players
                        count += 1
                        end_players = current_players
                        if current_players > peak_players:
                            peak_players = current_players
                        if 2 < current_players < lowest_players:
                            lowest_players = current_players
                except Exception as e:
                    error_message = f"Error during auction monitoring: {e}\n{traceback.format_exc()}"
                    print(error_message)
                    send_error_to_discord(error_message)

            end_time = int(time.time() * 1000)
            avg_players = total_players // count
            if lowest_players == float('inf'):
                lowest_players = "N/A"
            print(f"Dark Auction ended with {end_players} players at {datetime.fromtimestamp(end_time / 1000)}")
            print(f"Average players throughout the auction: {avg_players}")
            print(f"Peak players throughout the auction: {peak_players}")
            print(f"Lowest players throughout the auction: {lowest_players}")

            auction_duration = end_time - start_time
            auction_duration_formatted = format_time(auction_duration)
            print(f"Dark Auction ran for: {auction_duration_formatted}")

            embed = {
                "embeds": [
                    {
                        "title": "Dark Auction Summary",
                        "color": 3447003,
                        "fields": [
                            {"name": "Start Time", "value": str(datetime.fromtimestamp(start_time / 1000)), "inline": False},
                            {"name": "End Time", "value": str(datetime.fromtimestamp(end_time / 1000)), "inline": False},
                            {"name": "Auction Duration", "value": auction_duration_formatted, "inline": False},
                            {"name": "Starting Players", "value": str(start_players), "inline": True},
                            {"name": "Ending Players", "value": str(end_players), "inline": True},
                            {"name": "Average Players", "value": str(avg_players), "inline": True},
                            {"name": "Peak Players", "value": str(peak_players), "inline": True},
                            {"name": "Lowest Players", "value": str(lowest_players), "inline": True}
                        ],
                        "footer": {"text": "Skyblock Dark Auction Monitor"},
                        "timestamp": str(datetime.utcnow())
                    }
                ]
            }
            send_to_discord(embed)
        else:
            print("No Dark Auction found.")
            embed = {
                "embeds": [
                    {
                        "title": "Dark Auction Monitor",
                        "color": 15158332,
                        "description": "No Dark Auction detected within the expected window.",
                        "timestamp": str(datetime.utcnow())
                    }
                ]
            }
            send_to_discord(embed)
    except Exception as e:
        error_message = f"An error occurred during the Dark Auction monitoring: {e}\n{traceback.format_exc()}"
        print(error_message)
        send_error_to_discord(error_message)

def check_if_auction_running():
    try:
        skyblock_data = get_skyblock_data()
        return skyblock_data and 'dark_auction' in skyblock_data
    except Exception as e:
        error_message = f"Error in check_if_auction_running: {e}\n{traceback.format_exc()}"
        print(error_message)
        send_error_to_discord(error_message)
        return False

def main_loop():
    while True:
        try:
            if check_if_auction_running():
                start_time = int(time.time() * 1000) - (int(time.time() * 1000) % IRL_HOUR)
                print("Auction detected on startup. Monitoring current auction.")
                monitor_dark_auction(start_time)
            else:
                end_time = dark_auction_timer()
                print_timer(end_time)

                check_start_time = end_time
                check_end_time = end_time + 2 * 60 * 1000
                dark_auction_started = False

                while int(time.time() * 1000) < check_end_time:
                    try:
                        if int(time.time() * 1000) >= check_start_time:
                            skyblock_data = get_skyblock_data()
                            if skyblock_data and 'dark_auction' in skyblock_data:
                                monitor_dark_auction(check_start_time)
                                dark_auction_started = True
                                break
                        time.sleep(1)
                    except Exception as e:
                        error_message = f"Error while waiting for auction start: {e}\n{traceback.format_exc()}"
                        print(error_message)
                        send_error_to_discord(error_message)

                if not dark_auction_started:
                    print("No Dark Auction found within the expected window.")
        except Exception as e:
            error_message = f"An error occurred in the main loop: {e}\n{traceback.format_exc()}"
            print(error_message)
            send_error_to_discord(error_message)

if __name__ == "__main__":
    main_loop()