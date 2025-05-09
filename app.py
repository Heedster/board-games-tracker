import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
PRE_ORDERS_URL = "https://www.boardgamesindia.com/pre-orders?fq=1"
DYNAMODB_TABLE_NAME = "board-games-preorders"

def send_email(subject, body_html):
    # Create a new SES resource
    ses_client = boto3.client('ses')
    
    sender = os.getenv('SES_SENDER_EMAIL')
    recipient = os.getenv('RECEIVER_EMAIL')
    
    if not all([sender, recipient]):
        print("Email configuration missing")
        return
    
    try:
        response = ses_client.send_email(
            Destination={
                'ToAddresses': [recipient],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': 'UTF-8',
                        'Data': body_html,
                    },
                },
                'Subject': {
                    'Charset': 'UTF-8',
                    'Data': subject,
                },
            },
            Source=sender,
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
    except ClientError as e:
        print(f"Error sending email: {e.response['Error']['Message']}")
        raise

def send_error_notification(error_message):
    subject = "Board Games Pre-Order Monitor Error"
    body = f"""
    <h2>Board Games Pre-Order Monitor Error</h2>
    <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Error Message: {error_message}</p>
    <p>Please check the website and the monitor service.</p>
    """
    
    send_email(subject, body)

class PreOrderGameFetcher:
    def __init__(self, url=PRE_ORDERS_URL):
        self.url = url

    def fetch_games(self):
        try:
            print("Fetching webpage...")
            response = requests.get(self.url)
            response.raise_for_status()
            print(f"Response status: {response.status_code}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"Page title: {soup.title.text if soup.title else 'No title found'}")
            
            games = []
            # Find the main product grid
            product_grid = soup.select_one('div.main-products.product-grid')
            if not product_grid:
                error_msg = "Could not find product grid on the webpage. The website structure might have changed."
                print(error_msg)
                raise Exception(error_msg)
                
            # Find all product thumbs within the grid
            game_elements = product_grid.select('.product-thumb')
            print(f"Found {len(game_elements)} products")
            
            for game in game_elements:
                try:
                    # Get the game title and URL
                    name_element = game.select_one('.name a')
                    if not name_element:
                        continue
                        
                    title = name_element.text.strip()
                    url = name_element['href']
                    
                    # Get the price
                    price = None
                    price_new = game.select_one('.price-new')
                    price_normal = game.select_one('.price-normal')
                    
                    if price_new:
                        price = price_new.text.strip()
                    elif price_normal:
                        price = price_normal.text.strip()
                    
                    if not price:
                        print(f"Warning: Could not find price for {title}")
                        continue
                    
                    # Get stock status
                    stock_status = None
                    stock_element = game.select_one('.preorder-stock')
                    if stock_element:
                        stock_status = stock_element.text.strip()
                    
                    games.append({
                        'title': title,
                        'price': price,
                        'url': url,
                        'stock_status': stock_status
                    })
                    
                except Exception as e:
                    print(f"Error processing game: {str(e)}")
                    continue
            
            return games
            
        except Exception as e:
            error_msg = f"Error fetching pre-order games: {str(e)}"
            print(error_msg)
            raise

def get_pre_order_games():
    fetcher = PreOrderGameFetcher()
    return fetcher.fetch_games()

def load_previous_games():
    # Use DynamoDB to store the previous games list
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))
    
    try:
        response = table.get_item(
            Key={
                'id': 'current_games'
            }
        )
        if 'Item' in response:
            return response['Item']['games']
        return []
    except Exception as e:
        print(f"Error loading previous games: {str(e)}")
        return []

def save_current_games(games):
    # Use DynamoDB to store the current games list
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))
    
    try:
        table.put_item(
            Item={
                'id': 'current_games',
                'games': games,
                'last_updated': datetime.now().isoformat()
            }
        )
    except Exception as e:
        print(f"Error saving current games: {str(e)}")
        raise

def send_email_notification(new_games, removed_games):
    new_count = len(new_games)
    removed_count = len(removed_games)
    
    subject = f"Board Games Pre-Order Update: {new_count} New, {removed_count} Removed"
    body = f"""
    <h2>Board Games Pre-Order Update</h2>
    <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h3>New Games Available for Pre-Order ({new_count}):</h3>
    <ul>
    {''.join([f'<li>{game["title"]} - {game["price"]}</li>' for game in new_games])}
    </ul>
    
    <h3>Games No Longer Available for Pre-Order ({removed_count}):</h3>
    <ul>
    {''.join([f'<li>{game["title"]} - {game["price"]}</li>' for game in removed_games])}
    </ul>
    """
    
    send_email(subject, body)

def check_for_updates():
    """
    Check for updates in pre-order games without sending notifications.
    Returns a tuple of (current_games, new_games, removed_games)
    """
    try:
        current_games = get_pre_order_games()
        previous_games = load_previous_games()
        
        # Find new games
        new_games = [game for game in current_games if game not in previous_games]
        
        # Find removed games
        removed_games = [game for game in previous_games if game not in current_games]
        
        # Save current games for next comparison
        save_current_games(current_games)
        
        return current_games, new_games, removed_games
        
    except Exception as e:
        print(f"Error in check_for_updates: {str(e)}")
        raise

def process_updates_with_notification():
    """
    Check for updates and send notifications if there are changes.
    Returns a dictionary with the results.
    """
    try:
        current_games, new_games, removed_games = check_for_updates()
        
        if new_games or removed_games:
            send_email_notification(new_games, removed_games)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully checked for updates',
                'new_games_count': len(new_games),
                'removed_games_count': len(removed_games)
            })
        }
    except Exception as e:
        print(f"Error in process_updates_with_notification: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

# Lambda handler
def lambda_handler(event, context):
    return process_updates_with_notification() 