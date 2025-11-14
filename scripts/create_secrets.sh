#!/bin/bash

# Helper script to create Kubernetes secrets file from environment variables

echo "========================================="
echo "Kubernetes Secrets Generator"
echo "========================================="
echo ""

# Function to base64 encode
encode_base64() {
    echo -n "$1" | base64
}

# Collect inputs
read -p "Enter Django SECRET_KEY (or press Enter to generate): " SECRET_KEY
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
    echo "Generated SECRET_KEY: $SECRET_KEY"
fi

read -p "Enter OpenAI API Key: " OPENAI_API_KEY
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OpenAI API Key is required!"
    exit 1
fi

read -p "Enter DATABASE_URL (PostgreSQL connection string): " DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "Collecting database details separately..."
    read -p "Database Name: " DB_NAME
    read -p "Database User: " DB_USER
    read -s -p "Database Password: " DB_PASSWORD
    echo ""
    read -p "Database Host (RDS Endpoint): " DB_HOST
    DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:5432/${DB_NAME}"
else
    # Parse DATABASE_URL
    DB_NAME=$(echo $DATABASE_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    DB_USER=$(echo $DATABASE_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_PASSWORD=$(echo $DATABASE_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
fi

# Encode values
SECRET_KEY_B64=$(encode_base64 "$SECRET_KEY")
OPENAI_API_KEY_B64=$(encode_base64 "$OPENAI_API_KEY")
DATABASE_URL_B64=$(encode_base64 "$DATABASE_URL")
DB_NAME_B64=$(encode_base64 "$DB_NAME")
DB_USER_B64=$(encode_base64 "$DB_USER")
DB_PASSWORD_B64=$(encode_base64 "$DB_PASSWORD")
DB_HOST_B64=$(encode_base64 "$DB_HOST")

# Create secrets.yaml
cat > k8s/secrets.yaml <<EOF
# WARNING: This file contains sensitive data. DO NOT commit to version control!
apiVersion: v1
kind: Secret
metadata:
  name: resume-sorter-secrets
  namespace: resume-sorter
type: Opaque
data:
  SECRET_KEY: $SECRET_KEY_B64
  OPENAI_API_KEY: $OPENAI_API_KEY_B64
  DATABASE_URL: $DATABASE_URL_B64
  DB_NAME: $DB_NAME_B64
  DB_USER: $DB_USER_B64
  DB_PASSWORD: $DB_PASSWORD_B64
  DB_HOST: $DB_HOST_B64
EOF

echo ""
echo "✅ Secrets file created: k8s/secrets.yaml"
echo ""
echo "⚠️  IMPORTANT: This file contains sensitive data!"
echo "   - Do NOT commit it to version control"
echo "   - k8s/secrets.yaml is already in .gitignore"
echo ""
echo "You can now deploy with: ./deploy_to_eks.sh"
