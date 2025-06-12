# Board Games Monitor

This application monitors pre-order board games and new arrivals from BoardGamesIndia.com and sends email notifications when there are changes in either list.

## Features

- Daily monitoring of pre-order board games and new arrivals
- Email notifications for new and removed items in both categories
- Web interface to check if the service is running
- Email notifications via Amazon SES
- Serverless deployment using AWS SAM

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with the following variables:
   ```
   # AWS SES Configuration
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_REGION=your_aws_region  # e.g., us-east-1
   SES_SENDER_EMAIL=your_verified_ses_email
   RECEIVER_EMAIL=your_email@example.com
   ```

Note: Before using Amazon SES, you need to:
1. Create an AWS account if you don't have one
2. Verify your sender email address in SES
3. Request production access if you're not in the SES sandbox
4. Create IAM user with SES permissions and get access keys

## Deployment with AWS SAM

1. Install AWS SAM CLI if you haven't already
2. Build the SAM application:
   ```bash
   sam build
   ```
3. Deploy the application:
   ```bash
   sam deploy --guided
   ```
4. Follow the prompts to configure your deployment

The application will automatically check for updates every day at 9:00 AM and send email notifications if there are any changes in either the pre-order list or new arrivals.

## Local Development

To run the application locally:

```bash
python app.py
```

The application will be available at `http://localhost:5000` 