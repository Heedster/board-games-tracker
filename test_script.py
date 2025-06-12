from app import get_pre_order_games

if __name__ == '__main__':
    try:
        games = get_pre_order_games()
        print("\nSuccessfully parsed games:")
        for game in games:
            print(f"\nTitle: {game['title']}")
            print(f"Price: {game['price']}")
            print(f"URL: {game['url']}")
            if game['stock_status']:
                print(f"Stock Status: {game['stock_status']}")
    except Exception as e:
        print(f"Error occurred: {str(e)}") 