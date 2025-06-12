from app import get_pre_order_games, get_new_arrivals

def print_games(games, category):
    print(f"\n=== {category} ===")
    print(f"Total games found: {len(games)}")
    print("\nSuccessfully parsed games:")
    for game in games:
        print(f"\nTitle: {game['title']}")
        print(f"Price: {game['price']}")
        print(f"URL: {game['url']}")
        if game['stock_status']:
            print(f"Stock Status: {game['stock_status']}")

if __name__ == '__main__':
    try:
        # Test pre-orders
        pre_order_games = get_pre_order_games()
        print_games(pre_order_games, "PRE-ORDERS")
        
        # Test new arrivals
        new_arrivals = get_new_arrivals()
        print_games(new_arrivals, "NEW ARRIVALS")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}") 