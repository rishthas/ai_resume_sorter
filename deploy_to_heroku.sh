#!/bin/bash

# Heroku Deployment Script for AI Resume Sorter
# This script automates the deployment process to Heroku

set -e  # Exit on error

echo "========================================="
echo "AI Resume Sorter - Heroku Deployment"
echo "========================================="
echo ""

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI is not installed."
    echo "Please install it from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

echo "✅ Heroku CLI found"

# Check if user is logged in
if ! heroku auth:whoami &> /dev/null; then
    echo "Please login to Heroku:"
    heroku login
fi

echo "✅ Logged in to Heroku"
echo ""

# Ask for app name
read -p "Enter your Heroku app name (or press Enter to create a new one): " APP_NAME

if [ -z "$APP_NAME" ]; then
    echo "Creating new Heroku app..."
    heroku create
    APP_NAME=$(heroku apps:info --json | python3 -c "import sys, json; print(json.load(sys.stdin)['app']['name'])")
else
    echo "Using existing app: $APP_NAME"
    if ! heroku apps:info --app $APP_NAME &> /dev/null; then
        echo "App doesn't exist. Creating new app..."
        heroku create $APP_NAME
    fi
fi

echo "✅ App name: $APP_NAME"
echo ""

# Add PostgreSQL if not exists
echo "Checking for PostgreSQL addon..."
if ! heroku addons --app $APP_NAME | grep -q "heroku-postgresql"; then
    echo "Adding PostgreSQL addon..."
    heroku addons:create heroku-postgresql:essential-0 --app $APP_NAME
    echo "✅ PostgreSQL addon added"
else
    echo "✅ PostgreSQL addon already exists"
fi
echo ""

# Set environment variables
echo "Setting environment variables..."

read -p "Enter your OpenAI API Key: " OPENAI_KEY
if [ -z "$OPENAI_KEY" ]; then
    echo "❌ OpenAI API Key is required!"
    exit 1
fi

heroku config:set OPENAI_API_KEY=$OPENAI_KEY --app $APP_NAME

# Generate secret key
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
heroku config:set SECRET_KEY=$SECRET_KEY --app $APP_NAME

# Set other config
heroku config:set DEBUG=False --app $APP_NAME
heroku config:set ALLOWED_HOSTS=$APP_NAME.herokuapp.com --app $APP_NAME
heroku config:set MODEL=gpt-3.5-turbo --app $APP_NAME

echo "✅ Environment variables configured"
echo ""

# Commit changes if needed
echo "Checking for uncommitted changes..."
if ! git diff-index --quiet HEAD --; then
    echo "You have uncommitted changes."
    read -p "Commit changes now? (y/n): " COMMIT_CHOICE
    if [ "$COMMIT_CHOICE" = "y" ]; then
        git add .
        git commit -m "Prepare for Heroku deployment"
        echo "✅ Changes committed"
    fi
fi
echo ""

# Deploy to Heroku
echo "Deploying to Heroku..."
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
    git push heroku $CURRENT_BRANCH
else
    echo "Pushing branch $CURRENT_BRANCH to Heroku main..."
    git push heroku $CURRENT_BRANCH:main
fi

echo "✅ Code deployed"
echo ""

# Run migrations
echo "Running database migrations..."
heroku run python manage.py migrate --app $APP_NAME
echo "✅ Migrations complete"
echo ""

# Collect static files
echo "Collecting static files..."
heroku run python manage.py collectstatic --noinput --app $APP_NAME
echo "✅ Static files collected"
echo ""

# Ask to create superuser
read -p "Create a superuser for admin access? (y/n): " CREATE_SUPERUSER
if [ "$CREATE_SUPERUSER" = "y" ]; then
    heroku run python manage.py createsuperuser --app $APP_NAME
fi
echo ""

# Display app info
echo "========================================="
echo "🎉 Deployment Complete!"
echo "========================================="
echo ""
echo "App URL: https://$APP_NAME.herokuapp.com"
echo "Admin URL: https://$APP_NAME.herokuapp.com/admin"
echo ""
echo "Useful commands:"
echo "  View logs:    heroku logs --tail --app $APP_NAME"
echo "  Open app:     heroku open --app $APP_NAME"
echo "  Run shell:    heroku run python manage.py shell --app $APP_NAME"
echo "  Restart app:  heroku restart --app $APP_NAME"
echo ""
echo "Opening app in browser..."
heroku open --app $APP_NAME

echo ""
echo "Deployment successful! 🚀"
