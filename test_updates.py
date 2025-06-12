import json
from app import check_for_updates

def load_previous_games():
    try:
        with open('previous_games.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_current_games(games):
    with open('previous_games.json', 'w') as f:
        json.dump(games, f)

def print_game_list(games, title):
    print(f"\n{title} ({len(games)}):")
    for game in games:
        print(f"- {game['title']} ({game['price']})")
        if game['stock_status']:
            print(f"  Stock Status: {game['stock_status']}")

if __name__ == "__main__":
    try:
        current_data, pre_order_updates, new_arrival_updates = check_for_updates()
        
        print("\n=== Current State ===")
        print_game_list(current_data['pre_orders'], "Current Pre-Orders")
        print_game_list(current_data['new_arrivals'], "Current New Arrivals")
        
        print("\n=== Updates ===")
        print_game_list(pre_order_updates['new'], "New Pre-Orders")
        print_game_list(pre_order_updates['removed'], "Removed Pre-Orders")
        print_game_list(new_arrival_updates['new'], "New Arrivals")
        print_game_list(new_arrival_updates['removed'], "Removed from New Arrivals")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}") 