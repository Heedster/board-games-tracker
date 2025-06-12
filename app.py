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
NEW_ARRIVALS_URL = "https://www.boardgamesindia.com/new-arrivals?fq=1"
DYNAMODB_TABLE_NAME = "board-games-tracker"

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
    subject = "Board Games Monitor Error"
    body = f"""
    <h2>Board Games Monitor Error</h2>
    <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Error Message: {error_message}</p>
    <p>Please check the website and the monitor service.</p>
    """
    
    send_email(subject, body)

class GameFetcher:
    def __init__(self, url):
        self.url = url

    def fetch_games(self):
        try:
            print(f"Fetching webpage: {self.url}")
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
            error_msg = f"Error fetching games: {str(e)}"
            print(error_msg)
            raise

def get_pre_order_games():
    fetcher = GameFetcher(PRE_ORDERS_URL)
    return fetcher.fetch_games()

def get_new_arrivals():
    fetcher = GameFetcher(NEW_ARRIVALS_URL)
    return fetcher.fetch_games()

def load_previous_data():
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
            return response['Item']
        return {'pre_orders': [], 'new_arrivals': []}
    except Exception as e:
        print(f"Error loading previous data: {str(e)}")
        return {'pre_orders': [], 'new_arrivals': []}

def save_current_data(pre_orders, new_arrivals):
    # Use DynamoDB to store the current games list
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.getenv('DYNAMODB_TABLE_NAME'))
    
    try:
        table.put_item(
            Item={
                'id': 'current_games',
                'pre_orders': pre_orders,
                'new_arrivals': new_arrivals,
                'last_updated': datetime.now().isoformat()
            }
        )
    except Exception as e:
        print(f"Error saving current data: {str(e)}")
        raise

def send_email_notification(pre_order_updates, new_arrival_updates):
    new_pre_orders = pre_order_updates['new']
    removed_pre_orders = pre_order_updates['removed']
    new_arrivals = new_arrival_updates['new']
    removed_arrivals = new_arrival_updates['removed']
    
    subject = f"Board Games Update: {len(new_pre_orders)} New Pre-Orders, {len(removed_pre_orders)} Removed Pre-Orders, {len(new_arrivals)} New Arrivals"
    
    body = f"""
    <h2>Board Games Update</h2>
    <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h3>New Pre-Orders ({len(new_pre_orders)}):</h3>
    <ul>
    {''.join([f'<li><a href="{game["url"]}">{game["title"]}</a> - {game["price"]}</li>' for game in new_pre_orders])}
    </ul>
    
    <h3>Removed Pre-Orders ({len(removed_pre_orders)}):</h3>
    <ul>
    {''.join([f'<li>{game["title"]} - {game["price"]}</li>' for game in removed_pre_orders])}
    </ul>
    
    <h3>New Arrivals ({len(new_arrivals)}):</h3>
    <ul>
    {''.join([f'<li><a href="{game["url"]}">{game["title"]}</a> - {game["price"]}</li>' for game in new_arrivals])}
    </ul>
    
    <h3>Removed from New Arrivals ({len(removed_arrivals)}):</h3>
    <ul>
    {''.join([f'<li>{game["title"]} - {game["price"]}</li>' for game in removed_arrivals])}
    </ul>
    """
    
    send_email(subject, body)

def check_for_updates():
    """
    Check for updates in both pre-order games and new arrivals without sending notifications.
    Returns a tuple of (current_data, pre_order_updates, new_arrival_updates)
    """
    try:
        current_pre_orders = get_pre_order_games()
        current_new_arrivals = get_new_arrivals()
        previous_data = load_previous_data()
        
        # Find pre-order updates
        new_pre_orders = [game for game in current_pre_orders if game not in previous_data['pre_orders']]
        removed_pre_orders = [game for game in previous_data['pre_orders'] if game not in current_pre_orders]
        
        # Find new arrival updates
        new_arrivals = [game for game in current_new_arrivals if game not in previous_data['new_arrivals']]
        removed_arrivals = [game for game in previous_data['new_arrivals'] if game not in current_new_arrivals]
        
        # Save current data for next comparison
        save_current_data(current_pre_orders, current_new_arrivals)
        
        current_data = {
            'pre_orders': current_pre_orders,
            'new_arrivals': current_new_arrivals
        }
        
        pre_order_updates = {
            'new': new_pre_orders,
            'removed': removed_pre_orders
        }
        
        new_arrival_updates = {
            'new': new_arrivals,
            'removed': removed_arrivals
        }
        
        return current_data, pre_order_updates, new_arrival_updates
        
    except Exception as e:
        print(f"Error in check_for_updates: {str(e)}")
        raise

def process_updates_with_notification():
    """
    Check for updates and send notifications if there are changes.
    Returns a dictionary with the results.
    """
    try:
        current_data, pre_order_updates, new_arrival_updates = check_for_updates()
        
        if (pre_order_updates['new'] or pre_order_updates['removed'] or 
            new_arrival_updates['new'] or new_arrival_updates['removed']):
            send_email_notification(pre_order_updates, new_arrival_updates)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully checked for updates',
                'new_pre_orders_count': len(pre_order_updates['new']),
                'removed_pre_orders_count': len(pre_order_updates['removed']),
                'new_arrivals_count': len(new_arrival_updates['new']),
                'removed_arrivals_count': len(new_arrival_updates['removed'])
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