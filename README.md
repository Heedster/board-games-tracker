# Board Games Pre-Order Monitor

This application monitors pre-order board games from BoardGamesIndia.com and sends email notifications when there are changes in the available pre-orders.

## Features

- Daily monitoring of pre-order board games
- Email notifications for new and removed pre-orders
- Web interface to check if the service is running
- Free hosting on Render.com
- Email notifications via Amazon SES

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

## Deployment on Render.com

1. Create a new Web Service on Render.com
2. Connect your GitHub repository
3. Set the following environment variables in Render:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_REGION`
   - `SES_SENDER_EMAIL`
   - `RECEIVER_EMAIL`
4. Deploy the service

The application will automatically check for updates every day at 9:00 AM and send email notifications if there are any changes in the pre-order list.

## Local Development

To run the application locally:

```bash
python app.py
```

The application will be available at `http://localhost:5000` 