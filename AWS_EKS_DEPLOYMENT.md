# AWS EKS Deployment Guide - AI Resume Sorter

Complete guide for deploying the Django Resume Sorter application to AWS EKS (Elastic Kubernetes Service) with PostgreSQL RDS.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [AWS Infrastructure Setup](#aws-infrastructure-setup)
4. [Application Deployment](#application-deployment)
5. [Configuration](#configuration)
6. [Monitoring & Logging](#monitoring--logging)
7. [Scaling](#scaling)
8. [Maintenance](#maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Cost Optimization](#cost-optimization)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Internet/Users                        │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────▼──────────┐
          │  Application Load   │
          │     Balancer        │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │    AWS EKS Cluster  │
          │  ┌────────────────┐ │
          │  │  Resume Sorter │ │
          │  │  Pods (2-10)   │ │
          │  └────────┬───────┘ │
          └───────────│─────────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
┌──────▼─────┐ ┌────▼────┐  ┌────▼────┐
│ RDS        │ │  EFS    │  │   ECR   │
│ PostgreSQL │ │ Storage │  │ Registry│
└────────────┘ └─────────┘  └─────────┘
```

## Prerequisites

### Required Tools

1. **AWS CLI** (v2.x or later)
   ```bash
   # macOS
   brew install awscli

   # Linux
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install

   # Verify
   aws --version
   ```

2. **kubectl** (v1.25 or later)
   ```bash
   # macOS
   brew install kubectl

   # Linux
   curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
   sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

   # Verify
   kubectl version --client
   ```

3. **Docker** (v20.x or later)
   ```bash
   # Install from docker.com
   docker --version
   ```

4. **eksctl** (recommended for EKS cluster creation)
   ```bash
   # macOS
   brew install eksctl

   # Linux
   curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
   sudo mv /tmp/eksctl /usr/local/bin

   # Verify
   eksctl version
   ```

5. **Terraform** (optional, for infrastructure as code)
   ```bash
   brew install terraform
   ```

### AWS Account Requirements

- AWS Account with appropriate permissions
- IAM user with access keys or SSO configured
- Permissions needed:
  - EKS cluster management
  - EC2 instance management
  - RDS database creation
  - ECR repository management
  - EFS file system creation
  - IAM role creation
  - VPC and networking configuration

### Configure AWS CLI

```bash
aws configure
# Enter: AWS Access Key ID
# Enter: AWS Secret Access Key
# Enter: Default region (e.g., us-east-1)
# Enter: Default output format (json)

# Test configuration
aws sts get-caller-identity
```

## AWS Infrastructure Setup

### Step 1: Create VPC and Networking

Using eksctl (recommended):

```bash
# Set variables
export CLUSTER_NAME=resume-sorter-cluster
export AWS_REGION=us-east-1

# Create EKS cluster with managed node group
eksctl create cluster \
  --name $CLUSTER_NAME \
  --region $AWS_REGION \
  --version 1.28 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 4 \
  --managed \
  --with-oidc \
  --ssh-access \
  --ssh-public-key ~/.ssh/id_rsa.pub  # Optional: for SSH access

# This will take 15-20 minutes
```

The above command creates:
- VPC with public and private subnets
- Internet Gateway
- NAT Gateway
- Route tables
- Security groups
- EKS cluster
- Managed node group

### Step 2: Create RDS PostgreSQL Database

```bash
# Set variables
DB_NAME=resumesorterdb
DB_USERNAME=resumeadmin
DB_PASSWORD="YourSecurePassword123!"  # Change this!
DB_INSTANCE_CLASS=db.t3.micro

# Get VPC ID
VPC_ID=$(aws eks describe-cluster --name $CLUSTER_NAME --query "cluster.resourcesVpcConfig.vpcId" --output text)

# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name resume-sorter-db-subnet \
  --db-subnet-group-description "Subnet group for Resume Sorter RDS" \
  --subnet-ids $(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[?MapPublicIpOnLaunch==\`false\`].SubnetId" --output text)

# Create security group for RDS
RDS_SG_ID=$(aws ec2 create-security-group \
  --group-name resume-sorter-rds-sg \
  --description "Security group for Resume Sorter RDS" \
  --vpc-id $VPC_ID \
  --output text --query 'GroupId')

# Get EKS node security group
NODE_SG=$(aws eks describe-cluster --name $CLUSTER_NAME --query "cluster.resourcesVpcConfig.clusterSecurityGroupId" --output text)

# Allow traffic from EKS nodes to RDS
aws ec2 authorize-security-group-ingress \
  --group-id $RDS_SG_ID \
  --protocol tcp \
  --port 5432 \
  --source-group $NODE_SG

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier resume-sorter-db \
  --db-instance-class $DB_INSTANCE_CLASS \
  --engine postgres \
  --engine-version 15.4 \
  --master-username $DB_USERNAME \
  --master-user-password "$DB_PASSWORD" \
  --allocated-storage 20 \
  --db-name $DB_NAME \
  --vpc-security-group-ids $RDS_SG_ID \
  --db-subnet-group-name resume-sorter-db-subnet \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:04:00-sun:05:00" \
  --storage-encrypted \
  --multi-az

# Wait for RDS to be available (takes 5-10 minutes)
aws rds wait db-instance-available --db-instance-identifier resume-sorter-db

# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier resume-sorter-db --query "DBInstances[0].Endpoint.Address" --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"
echo "Database URL: postgresql://$DB_USERNAME:$DB_PASSWORD@$RDS_ENDPOINT:5432/$DB_NAME"
```

Save the Database URL for later use!

### Step 3: Create EFS File System

```bash
# Create EFS file system
EFS_ID=$(aws efs create-file-system \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --encrypted \
  --tags Key=Name,Value=resume-sorter-efs \
  --query 'FileSystemId' \
  --output text)

echo "EFS File System ID: $EFS_ID"

# Get subnet IDs
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[].SubnetId" --output text)

# Create security group for EFS
EFS_SG_ID=$(aws ec2 create-security-group \
  --group-name resume-sorter-efs-sg \
  --description "Security group for Resume Sorter EFS" \
  --vpc-id $VPC_ID \
  --output text --query 'GroupId')

# Allow NFS traffic from EKS nodes
aws ec2 authorize-security-group-ingress \
  --group-id $EFS_SG_ID \
  --protocol tcp \
  --port 2049 \
  --source-group $NODE_SG

# Create mount targets in each subnet
for subnet in $SUBNET_IDS; do
  aws efs create-mount-target \
    --file-system-id $EFS_ID \
    --subnet-id $subnet \
    --security-groups $EFS_SG_ID
done

# Install EFS CSI driver
kubectl apply -k "github.com/kubernetes-sigs/aws-efs-csi-driver/deploy/kubernetes/overlays/stable/?ref=master"

# Update pvc.yaml with EFS ID
sed -i.bak "s|<EFS_FILE_SYSTEM_ID>|$EFS_ID|g" k8s/pvc.yaml
rm -f k8s/pvc.yaml.bak
```

### Step 4: Install ALB Ingress Controller

```bash
# Create IAM policy for ALB controller
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.6.0/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

# Create IAM role and service account
eksctl create iamserviceaccount \
  --cluster=$CLUSTER_NAME \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy \
  --override-existing-serviceaccounts \
  --approve

# Install ALB controller using Helm
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=$CLUSTER_NAME \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

## Application Deployment

### Step 1: Create Kubernetes Secrets

Use the helper script:

```bash
./scripts/create_secrets.sh
```

Or manually create `k8s/secrets.yaml` from the example template and encode values:

```bash
# Encode values
echo -n "your-secret-key" | base64
echo -n "sk-..." | base64  # OpenAI API key
echo -n "postgresql://user:pass@host:5432/db" | base64
```

### Step 2: Build and Push Docker Image

The deployment script handles this automatically, or manually:

```bash
# Set variables
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION=us-east-1
export ECR_REPO=resume-sorter

# Create ECR repository
aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION

# Build image
docker build -t $ECR_REPO:latest .

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag and push
docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
```

### Step 3: Deploy to EKS

Using the automated script:

```bash
./deploy_to_eks.sh
```

Or manually:

```bash
# Apply manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml

# Run migrations
kubectl apply -f k8s/migration-job.yaml
kubectl wait --for=condition=complete --timeout=300s job/resume-sorter-migrate -n resume-sorter

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

### Step 4: Verify Deployment

```bash
# Check pods
kubectl get pods -n resume-sorter

# Check services
kubectl get svc -n resume-sorter

# Check ingress
kubectl get ingress -n resume-sorter

# Get application URL
kubectl get svc resume-sorter-service -n resume-sorter -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

## Configuration

### Environment Variables

All configuration is managed through Kubernetes ConfigMaps and Secrets:

**ConfigMap** (`k8s/configmap.yaml`):
- `DEBUG`: Set to "False" for production
- `ALLOWED_HOSTS`: Domain names and ALB DNS
- `MODEL`: OpenAI model (gpt-3.5-turbo, gpt-4, etc.)

**Secrets** (`k8s/secrets.yaml`):
- `SECRET_KEY`: Django secret key
- `OPENAI_API_KEY`: OpenAI API key
- `DATABASE_URL`: PostgreSQL connection string
- Database credentials (name, user, password, host)

### Updating Configuration

```bash
# Edit ConfigMap
kubectl edit configmap resume-sorter-config -n resume-sorter

# Update secrets (recreate secrets.yaml and apply)
kubectl apply -f k8s/secrets.yaml

# Restart deployment to pick up changes
kubectl rollout restart deployment/resume-sorter -n resume-sorter
```

### Custom Domain Setup

1. **Get ALB DNS**:
   ```bash
   kubectl get ingress resume-sorter-ingress -n resume-sorter -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
   ```

2. **Create DNS Record**:
   - In Route 53 or your DNS provider
   - Create CNAME or ALIAS record pointing to ALB DNS

3. **Request ACM Certificate**:
   ```bash
   aws acm request-certificate \
     --domain-name resume-sorter.yourdomain.com \
     --validation-method DNS \
     --region $AWS_REGION
   ```

4. **Update Ingress**:
   Edit `k8s/ingress.yaml` and add certificate ARN:
   ```yaml
   annotations:
     alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:region:account:certificate/id
   ```

5. **Apply changes**:
   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```

## Monitoring & Logging

### CloudWatch Container Insights

```bash
# Install CloudWatch agent
eksctl utils install-cloudwatch-observability \
  --cluster $CLUSTER_NAME \
  --region $AWS_REGION
```

### View Logs

```bash
# Pod logs
kubectl logs -f deployment/resume-sorter -n resume-sorter

# All pods
kubectl logs -f -l app=resume-sorter -n resume-sorter

# Previous pod (if crashed)
kubectl logs --previous deployment/resume-sorter -n resume-sorter
```

### Metrics and Monitoring

```bash
# Install metrics server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# View pod metrics
kubectl top pods -n resume-sorter

# View node metrics
kubectl top nodes
```

## Scaling

### Manual Scaling

```bash
# Scale pods
kubectl scale deployment resume-sorter --replicas=5 -n resume-sorter

# Scale nodes
eksctl scale nodegroup --cluster=$CLUSTER_NAME --nodes=4 standard-workers
```

### Auto-scaling

HPA (Horizontal Pod Autoscaler) is already configured in `k8s/hpa.yaml`:
- Min replicas: 2
- Max replicas: 10
- CPU target: 70%
- Memory target: 80%

View HPA status:
```bash
kubectl get hpa -n resume-sorter
kubectl describe hpa resume-sorter-hpa -n resume-sorter
```

### Cluster Autoscaler

```bash
# Enable cluster autoscaler
eksctl create iamserviceaccount \
  --cluster=$CLUSTER_NAME \
  --namespace=kube-system \
  --name=cluster-autoscaler \
  --attach-policy-arn=arn:aws:iam::aws:policy/AutoScalingFullAccess \
  --override-existing-serviceaccounts \
  --approve

kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

kubectl -n kube-system annotate deployment.apps/cluster-autoscaler cluster-autoscaler.kubernetes.io/safe-to-evict="false"

kubectl -n kube-system set image deployment.apps/cluster-autoscaler cluster-autoscaler=k8s.gcr.io/autoscaling/cluster-autoscaler:v1.28.0
```

## Maintenance

### Update Application

```bash
# Build new image
docker build -t resume-sorter:v2 .

# Tag and push
docker tag resume-sorter:v2 $ECR_URI:v2
docker push $ECR_URI:v2

# Update deployment
kubectl set image deployment/resume-sorter resume-sorter=$ECR_URI:v2 -n resume-sorter

# Monitor rollout
kubectl rollout status deployment/resume-sorter -n resume-sorter

# Rollback if needed
kubectl rollout undo deployment/resume-sorter -n resume-sorter
```

### Database Migrations

```bash
# Run migrations manually
kubectl delete job resume-sorter-migrate -n resume-sorter
kubectl apply -f k8s/migration-job.yaml
kubectl wait --for=condition=complete job/resume-sorter-migrate -n resume-sorter

# Or exec into a pod
kubectl exec -it deployment/resume-sorter -n resume-sorter -- python manage.py migrate
```

### Backup and Restore

**RDS Automated Backups**:
- Enabled by default (7-day retention)
- Backup window: 03:00-04:00 UTC

**Manual RDS Snapshot**:
```bash
aws rds create-db-snapshot \
  --db-instance-identifier resume-sorter-db \
  --db-snapshot-identifier resume-sorter-snapshot-$(date +%Y%m%d)
```

**Restore from Snapshot**:
```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier resume-sorter-db-restored \
  --db-snapshot-identifier resume-sorter-snapshot-YYYYMMDD
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n resume-sorter

# Describe pod for events
kubectl describe pod <pod-name> -n resume-sorter

# Check logs
kubectl logs <pod-name> -n resume-sorter
```

### Database Connection Issues

```bash
# Test database connectivity
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- psql $DATABASE_URL

# Check security groups
# Ensure RDS security group allows traffic from EKS nodes
```

### Image Pull Errors

```bash
# Verify ECR permissions
aws ecr get-login-password --region $AWS_REGION

# Check image exists
aws ecr describe-images --repository-name resume-sorter --region $AWS_REGION
```

### LoadBalancer Not Created

```bash
# Check ALB controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Verify IAM permissions
kubectl get sa aws-load-balancer-controller -n kube-system -o yaml
```

## Cost Optimization

### Monthly Cost Estimate

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| EKS Cluster | 1 cluster | $73/month |
| EC2 Nodes | 2 x t3.medium | ~$60/month |
| RDS PostgreSQL | db.t3.micro | ~$15/month |
| EFS | 10 GB storage | ~$3/month |
| ALB | 1 load balancer | ~$16/month |
| Data Transfer | Minimal | ~$5/month |
| **Total** | | **~$172/month** |

*Plus OpenAI API costs based on usage*

### Cost Saving Tips

1. **Use Spot Instances**:
   ```bash
   eksctl create nodegroup \
     --cluster=$CLUSTER_NAME \
     --spot \
     --instance-types=t3.medium,t3a.medium
   ```

2. **Use Fargate for low-traffic periods**:
   ```bash
   eksctl create fargateprofile \
     --cluster=$CLUSTER_NAME \
     --name resume-sorter-fargate \
     --namespace resume-sorter
   ```

3. **Schedule downtime** (dev/test environments):
   - Scale down to 0 replicas during off-hours
   - Use CronJobs to automate

4. **Right-size resources**:
   - Monitor actual usage
   - Adjust requests/limits in deployment.yaml
   - Use smaller RDS instance if appropriate

5. **Use Reserved Instances** (production):
   - 1-year or 3-year commitment
   - Up to 72% savings

## Security Best Practices

1. **Network Security**:
   - Use private subnets for RDS
   - Restrict security group rules
   - Enable VPC Flow Logs

2. **Secrets Management**:
   - Use AWS Secrets Manager (alternative to Kubernetes secrets)
   - Rotate credentials regularly
   - Never commit secrets to git

3. **Pod Security**:
   - Run as non-root user (already configured)
   - Use Pod Security Standards
   - Limit capabilities

4. **Image Security**:
   - Enable ECR image scanning
   - Use minimal base images
   - Regular updates

5. **IAM**:
   - Use IRSA (IAM Roles for Service Accounts)
   - Principle of least privilege
   - Regular audit

## Cleanup

To delete all resources:

```bash
# Delete Kubernetes resources
kubectl delete namespace resume-sorter

# Delete ALB controller
helm uninstall aws-load-balancer-controller -n kube-system

# Delete EFS
aws efs delete-file-system --file-system-id $EFS_ID

# Delete RDS
aws rds delete-db-instance \
  --db-instance-identifier resume-sorter-db \
  --skip-final-snapshot

# Delete EKS cluster
eksctl delete cluster --name $CLUSTER_NAME --region $AWS_REGION

# Delete ECR repository
aws ecr delete-repository --repository-name resume-sorter --force --region $AWS_REGION
```

## Additional Resources

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS ALB Ingress Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [eksctl Documentation](https://eksctl.io/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/)

## Support

For issues specific to:
- **AWS**: AWS Support Console
- **Kubernetes**: Kubernetes Slack
- **Django**: Django Forum
- **Application**: GitHub Issues

---

**Deployment Complete!** 🚀

Your Resume Sorter application is now running on AWS EKS with enterprise-grade reliability, scalability, and security!
