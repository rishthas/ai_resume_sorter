# Kubernetes Manifests for Resume Sorter

This directory contains all Kubernetes manifest files for deploying the Resume Sorter application to AWS EKS.

## Files Overview

| File | Purpose |
|------|---------|
| `namespace.yaml` | Creates the resume-sorter namespace |
| `configmap.yaml` | Non-sensitive configuration (DEBUG, ALLOWED_HOSTS, etc.) |
| `secrets.yaml.example` | Template for creating secrets (DO NOT COMMIT actual secrets.yaml!) |
| `deployment.yaml` | Main application deployment with 2 replicas |
| `service.yaml` | LoadBalancer service exposing the application |
| `ingress.yaml` | ALB Ingress for external access with SSL |
| `pvc.yaml` | PersistentVolumeClaim for media files (EFS) |
| `migration-job.yaml` | Kubernetes Job for running database migrations |
| `hpa.yaml` | HorizontalPodAutoscaler for auto-scaling (2-10 pods) |

## Quick Start

### 1. Create Secrets File

```bash
# Use the helper script
../scripts/create_secrets.sh

# Or copy and manually edit
cp secrets.yaml.example secrets.yaml
# Edit secrets.yaml with base64-encoded values
```

### 2. Update Placeholders

The deployment script (`../deploy_to_eks.sh`) automatically updates these, but if deploying manually:

- Replace `<AWS_ACCOUNT_ID>` with your AWS account ID
- Replace `<AWS_REGION>` with your AWS region (e.g., us-east-1)
- Replace `<EFS_FILE_SYSTEM_ID>` in pvc.yaml with your EFS ID
- Update domain in `ingress.yaml`

### 3. Deploy

```bash
# Automated deployment
../deploy_to_eks.sh

# Or manual deployment
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f configmap.yaml
kubectl apply -f pvc.yaml
kubectl apply -f migration-job.yaml
kubectl wait --for=condition=complete job/resume-sorter-migrate -n resume-sorter
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml
```

## Resource Specifications

### Deployment

- **Replicas**: 2 (can scale 2-10 with HPA)
- **Strategy**: RollingUpdate (maxSurge: 1, maxUnavailable: 0)
- **Image**: ECR container image
- **Resources**:
  - Requests: 250m CPU, 512Mi memory
  - Limits: 500m CPU, 1Gi memory

### Service

- **Type**: LoadBalancer
- **Port**: 80 (external) -> 8000 (container)
- **Protocol**: TCP

### Ingress

- **Class**: ALB (AWS Application Load Balancer)
- **Features**:
  - Internet-facing
  - HTTP to HTTPS redirect
  - SSL termination (requires ACM certificate)
  - Health checks

### Storage

- **Type**: EFS (Elastic File System)
- **Access Mode**: ReadWriteMany (shared across pods)
- **Capacity**: 10Gi
- **Mount Point**: /app/media

## Environment Variables

### From ConfigMap (non-sensitive)

- `DEBUG`: Django debug mode (False in production)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `MODEL`: OpenAI model to use (default: gpt-3.5-turbo)

### From Secrets (sensitive)

- `SECRET_KEY`: Django secret key
- `OPENAI_API_KEY`: OpenAI API key for resume analysis
- `DATABASE_URL`: PostgreSQL connection string
- Database credentials: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`

## Common Operations

### View Resources

```bash
kubectl get all -n resume-sorter
kubectl get pods -n resume-sorter
kubectl get svc -n resume-sorter
kubectl get ingress -n resume-sorter
```

### View Logs

```bash
kubectl logs -f deployment/resume-sorter -n resume-sorter
kubectl logs -f -l app=resume-sorter -n resume-sorter --all-containers=true
```

### Scale Manually

```bash
kubectl scale deployment resume-sorter --replicas=5 -n resume-sorter
```

### Update Configuration

```bash
# Edit ConfigMap
kubectl edit configmap resume-sorter-config -n resume-sorter

# Restart pods to pick up changes
kubectl rollout restart deployment/resume-sorter -n resume-sorter
```

### Run Migrations

```bash
kubectl delete job resume-sorter-migrate -n resume-sorter --ignore-not-found
kubectl apply -f migration-job.yaml
kubectl logs -f job/resume-sorter-migrate -n resume-sorter
```

### Execute Commands in Pod

```bash
# Get shell access
kubectl exec -it deployment/resume-sorter -n resume-sorter -- /bin/bash

# Run Django management commands
kubectl exec -it deployment/resume-sorter -n resume-sorter -- python manage.py createsuperuser
kubectl exec -it deployment/resume-sorter -n resume-sorter -- python manage.py shell
```

### Update Application

```bash
# After pushing new image to ECR
kubectl rollout restart deployment/resume-sorter -n resume-sorter

# Monitor rollout
kubectl rollout status deployment/resume-sorter -n resume-sorter

# Rollback if needed
kubectl rollout undo deployment/resume-sorter -n resume-sorter
```

### Get Application URL

```bash
# LoadBalancer URL
kubectl get svc resume-sorter-service -n resume-sorter -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Ingress URL (if custom domain configured)
kubectl get ingress resume-sorter-ingress -n resume-sorter -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
```

## Health Checks

The deployment includes:

**Liveness Probe**:
- Checks if the application is running
- Path: `/`
- Initial delay: 60s
- Period: 10s
- Failure threshold: 3

**Readiness Probe**:
- Checks if the application is ready to serve traffic
- Path: `/`
- Initial delay: 30s
- Period: 5s
- Failure threshold: 3

## Auto-scaling (HPA)

Configured to scale based on:
- CPU utilization: 70% target
- Memory utilization: 80% target
- Min replicas: 2
- Max replicas: 10

View HPA status:
```bash
kubectl get hpa -n resume-sorter
kubectl describe hpa resume-sorter-hpa -n resume-sorter
```

## Security Considerations

1. **Never commit secrets.yaml** - It's already in .gitignore
2. **Use secrets.yaml.example** as template only
3. **Rotate secrets regularly** - Update secrets.yaml and reapply
4. **Limit RBAC** - Use least privilege principle
5. **Network policies** - Consider adding NetworkPolicy for pod-to-pod communication
6. **Pod security** - Application runs as non-root user (UID 1000)

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod <pod-name> -n resume-sorter
kubectl logs <pod-name> -n resume-sorter
```

### Database connection issues

```bash
# Check secrets
kubectl get secret resume-sorter-secrets -n resume-sorter -o yaml

# Test database connection from pod
kubectl exec -it deployment/resume-sorter -n resume-sorter -- env | grep DATABASE
```

### Image pull errors

```bash
# Check if image exists
aws ecr describe-images --repository-name resume-sorter

# Verify node IAM role has ECR pull permissions
```

### LoadBalancer not provisioning

```bash
# Check ALB controller logs
kubectl logs -n kube-system deployment/aws-load-balancer-controller

# Verify service
kubectl describe svc resume-sorter-service -n resume-sorter
```

## Cleanup

To remove all resources:

```bash
kubectl delete namespace resume-sorter
```

This will delete:
- All pods
- Services
- Ingress
- ConfigMaps
- Secrets
- PVCs
- Jobs
- HPA

**Note**: This does NOT delete:
- EKS cluster
- RDS database
- EFS file system
- ECR images

See `../AWS_EKS_DEPLOYMENT.md` for full cleanup instructions.

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [ALB Ingress Controller](https://kubernetes-sigs.github.io/aws-load-balancer-controller/)
- [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
