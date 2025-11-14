#!/bin/bash

# AWS EKS Deployment Script for AI Resume Sorter
# This script automates the deployment process to AWS EKS

set -e  # Exit on error

echo "========================================="
echo "AI Resume Sorter - AWS EKS Deployment"
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
ECR_REPOSITORY_NAME="resume-sorter"
EKS_CLUSTER_NAME=${EKS_CLUSTER_NAME:-resume-sorter-cluster}
NAMESPACE="resume-sorter"

# Functions
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# Check prerequisites
echo "Checking prerequisites..."
check_command aws
check_command kubectl
check_command docker
print_success "All required commands are available"
echo ""

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_info "AWS Account ID: $AWS_ACCOUNT_ID"
print_info "AWS Region: $AWS_REGION"
echo ""

# Ask for confirmation
read -p "Continue with deployment? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Deployment cancelled."
    exit 0
fi
echo ""

# Step 1: Create ECR repository if it doesn't exist
echo "Step 1: Setting up ECR repository..."
if aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION &> /dev/null; then
    print_info "ECR repository already exists"
else
    aws ecr create-repository \
        --repository-name $ECR_REPOSITORY_NAME \
        --region $AWS_REGION \
        --image-scanning-configuration scanOnPush=true
    print_success "ECR repository created"
fi

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}"
print_info "ECR URI: $ECR_URI"
echo ""

# Step 2: Build Docker image
echo "Step 2: Building Docker image..."
docker build -t $ECR_REPOSITORY_NAME:latest .
print_success "Docker image built"
echo ""

# Step 3: Login to ECR
echo "Step 3: Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI
print_success "Logged into ECR"
echo ""

# Step 4: Tag and push image
echo "Step 4: Pushing image to ECR..."
docker tag $ECR_REPOSITORY_NAME:latest $ECR_URI:latest
docker tag $ECR_REPOSITORY_NAME:latest $ECR_URI:$(git rev-parse --short HEAD)
docker push $ECR_URI:latest
docker push $ECR_URI:$(git rev-parse --short HEAD)
print_success "Image pushed to ECR"
echo ""

# Step 5: Update kubeconfig
echo "Step 5: Configuring kubectl..."
aws eks update-kubeconfig --region $AWS_REGION --name $EKS_CLUSTER_NAME
print_success "kubectl configured for EKS cluster"
echo ""

# Step 6: Update Kubernetes manifests
echo "Step 6: Updating Kubernetes manifests..."
for file in k8s/*.yaml; do
    if [ "$file" != "k8s/secrets.yaml.example" ]; then
        sed -i.bak "s|<AWS_ACCOUNT_ID>|${AWS_ACCOUNT_ID}|g" "$file"
        sed -i.bak "s|<AWS_REGION>|${AWS_REGION}|g" "$file"
        rm -f "${file}.bak"
    fi
done
print_success "Kubernetes manifests updated"
echo ""

# Step 7: Check for secrets file
echo "Step 7: Checking secrets configuration..."
if [ ! -f "k8s/secrets.yaml" ]; then
    print_error "k8s/secrets.yaml not found!"
    echo "Please create k8s/secrets.yaml from k8s/secrets.yaml.example"
    echo "and fill in your actual values (base64 encoded)."
    echo ""
    echo "To encode values:"
    echo "  echo -n 'your-value' | base64"
    exit 1
fi
print_success "Secrets file found"
echo ""

# Step 8: Apply Kubernetes manifests
echo "Step 8: Deploying to Kubernetes..."

# Create namespace
kubectl apply -f k8s/namespace.yaml
print_success "Namespace created/updated"

# Apply secrets and configmap
kubectl apply -f k8s/secrets.yaml
print_success "Secrets applied"

kubectl apply -f k8s/configmap.yaml
print_success "ConfigMap applied"

# Apply PVC
kubectl apply -f k8s/pvc.yaml
print_success "PersistentVolumeClaim created"

# Run database migration job
echo ""
print_info "Running database migrations..."
kubectl delete job resume-sorter-migrate -n $NAMESPACE --ignore-not-found=true
kubectl apply -f k8s/migration-job.yaml

# Wait for migration to complete
echo "Waiting for migrations to complete..."
kubectl wait --for=condition=complete --timeout=300s job/resume-sorter-migrate -n $NAMESPACE
print_success "Database migrations completed"

# Apply deployment
kubectl apply -f k8s/deployment.yaml
print_success "Deployment created/updated"

# Apply service
kubectl apply -f k8s/service.yaml
print_success "Service created/updated"

# Apply ingress
kubectl apply -f k8s/ingress.yaml
print_success "Ingress created/updated"

# Apply HPA
kubectl apply -f k8s/hpa.yaml
print_success "HorizontalPodAutoscaler created/updated"

echo ""
print_success "Deployment completed successfully!"
echo ""

# Step 9: Get deployment status
echo "Deployment Status:"
echo "========================================="
kubectl get pods -n $NAMESPACE
echo ""
kubectl get svc -n $NAMESPACE
echo ""
kubectl get ingress -n $NAMESPACE
echo ""

# Get LoadBalancer URL
echo "Getting application URL..."
LB_HOSTNAME=$(kubectl get svc resume-sorter-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
if [ -n "$LB_HOSTNAME" ]; then
    print_success "Application URL: http://$LB_HOSTNAME"
else
    print_info "LoadBalancer is still provisioning. Run this command to get the URL:"
    echo "  kubectl get svc resume-sorter-service -n $NAMESPACE"
fi

echo ""
echo "========================================="
echo "Useful commands:"
echo "  View pods:       kubectl get pods -n $NAMESPACE"
echo "  View logs:       kubectl logs -f deployment/resume-sorter -n $NAMESPACE"
echo "  View services:   kubectl get svc -n $NAMESPACE"
echo "  View ingress:    kubectl get ingress -n $NAMESPACE"
echo "  Scale:           kubectl scale deployment resume-sorter --replicas=3 -n $NAMESPACE"
echo "  Restart:         kubectl rollout restart deployment/resume-sorter -n $NAMESPACE"
echo "========================================="
echo ""
print_success "Deployment complete! 🚀"
