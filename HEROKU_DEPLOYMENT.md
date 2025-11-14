# Heroku Deployment Guide for AI Resume Sorter

This guide will help you deploy the Django Resume Sorter application to Heroku.

## Prerequisites

1. **Heroku Account**: Sign up at [heroku.com](https://signup.heroku.com/)
2. **Heroku CLI**: Install from [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3. **Git**: Ensure git is installed and configured
4. **OpenAI API Key**: Get your API key from [platform.openai.com](https://platform.openai.com)

## Quick Deployment Steps

### 1. Install Heroku CLI

**macOS:**
```bash
brew tap heroku/brew && brew install heroku
```

**Windows:**
Download the installer from Heroku website

**Linux:**
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

### 2. Login to Heroku

```bash
heroku login
```

This will open your browser for authentication.

### 3. Create a New Heroku App

```bash
# Create app with a specific name
heroku create your-resume-sorter-app

# Or let Heroku generate a random name
heroku create
```

This creates a new Heroku app and adds a git remote named `heroku`.

### 4. Add PostgreSQL Database

Heroku apps need a database addon. Add the free PostgreSQL addon:

```bash
heroku addons:create heroku-postgresql:essential-0
```

This automatically sets the `DATABASE_URL` environment variable.

### 5. Set Environment Variables

Set your OpenAI API key and other configuration:

```bash
# Required: OpenAI API Key
heroku config:set OPENAI_API_KEY=your_openai_api_key_here

# Required: Django Secret Key (generate a secure random string)
heroku config:set SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Required: Disable Debug mode in production
heroku config:set DEBUG=False

# Required: Set allowed hosts (replace with your app name)
heroku config:set ALLOWED_HOSTS=your-resume-sorter-app.herokuapp.com

# Optional: Set AI model (default is gpt-3.5-turbo)
heroku config:set MODEL=gpt-3.5-turbo

# Optional: Disable static file collection (we'll do it manually)
heroku config:set DISABLE_COLLECTSTATIC=1
```

**Important**: Replace `your-resume-sorter-app.herokuapp.com` with your actual Heroku app URL.

### 6. Deploy to Heroku

```bash
# Make sure all changes are committed
git add .
git commit -m "Prepare for Heroku deployment"

# Push to Heroku
git push heroku main
```

If you're on a different branch (like `claude/django-resume-upload-...`), use:
```bash
git push heroku your-branch-name:main
```

### 7. Run Database Migrations

After deployment, run migrations to set up the database:

```bash
heroku run python manage.py migrate
```

### 8. Create a Superuser (Optional)

To access the Django admin panel:

```bash
heroku run python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 9. Collect Static Files

```bash
heroku run python manage.py collectstatic --noinput
```

### 10. Open Your App

```bash
heroku open
```

This opens your deployed application in the browser!

## Verification & Testing

### Check if the app is running:

```bash
heroku ps
```

You should see a web dyno running.

### View logs:

```bash
# View recent logs
heroku logs --tail

# View last 500 lines
heroku logs -n 500
```

### Test the application:

1. Visit your app URL (e.g., `https://your-app-name.herokuapp.com`)
2. Try uploading a test ZIP file with resumes
3. Verify the results are displayed correctly

## Common Issues & Solutions

### Issue 1: Application Error / 503

**Solution**: Check the logs:
```bash
heroku logs --tail
```

Common causes:
- Missing environment variables
- Database migration not run
- Dependencies not installed

### Issue 2: Static Files Not Loading

**Solution**:
```bash
# Collect static files
heroku run python manage.py collectstatic --noinput

# Verify DISABLE_COLLECTSTATIC is set correctly
heroku config:get DISABLE_COLLECTSTATIC
```

### Issue 3: Database Connection Error

**Solution**: Verify PostgreSQL addon is installed:
```bash
heroku addons
```

Should show `heroku-postgresql`.

### Issue 4: OpenAI API Errors

**Solution**: Check your API key is set:
```bash
heroku config:get OPENAI_API_KEY
```

Verify the key is correct and has sufficient credits.

### Issue 5: File Upload Errors

**Solution**: Heroku has ephemeral filesystem. Uploaded files are stored temporarily.

For persistent storage, consider:
- AWS S3
- Cloudinary
- Heroku's own persistent storage solutions

## Managing Your App

### View all config variables:
```bash
heroku config
```

### Set a new config variable:
```bash
heroku config:set VARIABLE_NAME=value
```

### Unset a config variable:
```bash
heroku config:unset VARIABLE_NAME
```

### Scale dynos:
```bash
# Scale to 1 web dyno (free tier)
heroku ps:scale web=1

# Scale to 2 web dynos (requires paid plan)
heroku ps:scale web=2
```

### Restart the app:
```bash
heroku restart
```

### Open Django shell:
```bash
heroku run python manage.py shell
```

### Access database:
```bash
heroku pg:psql
```

## Updating Your App

When you make changes to your code:

```bash
# Commit your changes
git add .
git commit -m "Your commit message"

# Push to Heroku
git push heroku main

# Run migrations if models changed
heroku run python manage.py migrate

# Restart if needed
heroku restart
```

## Cost Considerations

### Heroku Costs:
- **Eco Dyno**: ~$5/month (sleeps after 30 min of inactivity)
- **Basic Dyno**: ~$7/month (never sleeps)
- **PostgreSQL Essential-0**: $5/month (up to 10,000 rows)
- **PostgreSQL Essential-1**: $50/month (up to 10M rows)

### OpenAI API Costs:
- Varies based on usage and model selected
- gpt-3.5-turbo: Most cost-effective
- gpt-4: Higher accuracy, higher cost

### Optimization Tips:
1. Use gpt-3.5-turbo for development
2. Set appropriate timeout limits
3. Monitor your OpenAI usage dashboard
4. Consider caching results for repeated queries

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key | `sk-proj-abc123...` |
| `SECRET_KEY` | Yes | Django secret key | Auto-generated |
| `DEBUG` | Yes | Debug mode (False for production) | `False` |
| `ALLOWED_HOSTS` | Yes | Comma-separated list of allowed hosts | `yourapp.herokuapp.com` |
| `DATABASE_URL` | Auto | PostgreSQL connection string | Auto-set by Heroku |
| `MODEL` | No | OpenAI model to use | `gpt-3.5-turbo` |

## Custom Domain (Optional)

To use your own domain:

```bash
# Add a custom domain
heroku domains:add www.yourdomain.com

# Get DNS target
heroku domains

# Update ALLOWED_HOSTS
heroku config:set ALLOWED_HOSTS=www.yourdomain.com,yourdomain.com,yourapp.herokuapp.com
```

Then configure your DNS provider to point to the Heroku DNS target.

## SSL/HTTPS

Heroku provides automatic SSL certificates for all apps. HTTPS is enabled by default.

## Monitoring & Performance

### View app metrics:
```bash
heroku dashboard
```

Or visit: https://dashboard.heroku.com/apps/your-app-name

### Install New Relic (optional):
```bash
heroku addons:create newrelic:wayne
```

### Enable Papertrail for better logging:
```bash
heroku addons:create papertrail
heroku addons:open papertrail
```

## Backup & Restore

### Create a backup:
```bash
heroku pg:backups:capture
```

### List backups:
```bash
heroku pg:backups
```

### Restore from backup:
```bash
heroku pg:backups:restore b001
```

### Download backup:
```bash
heroku pg:backups:download
```

## Troubleshooting Commands

```bash
# Check dyno status
heroku ps

# View logs (real-time)
heroku logs --tail

# View logs (specific source)
heroku logs --source app --tail

# Restart app
heroku restart

# Run bash on Heroku
heroku run bash

# Check buildpack
heroku buildpacks

# Check environment variables
heroku config
```

## Security Best Practices

1. **Never commit sensitive data**: Keep `.env` in `.gitignore`
2. **Use strong SECRET_KEY**: Generate with `get_random_secret_key()`
3. **Keep DEBUG=False** in production
4. **Use environment variables**: For all sensitive configuration
5. **Regular updates**: Keep dependencies updated
6. **Monitor logs**: Check for suspicious activity
7. **Limit file uploads**: Set appropriate size limits
8. **API rate limiting**: Implement rate limiting for API calls

## Scaling Considerations

### When to scale:
- Response times increase
- High dyno load
- Database reaching capacity
- Many concurrent users

### How to scale:
```bash
# Vertical scaling (upgrade dyno type)
heroku ps:type web=standard-1x

# Horizontal scaling (more dynos)
heroku ps:scale web=2

# Database scaling
heroku addons:create heroku-postgresql:standard-0
```

## Development vs Production

### Local Development:
```bash
# Use .env file
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

### Production (Heroku):
```bash
# Use config vars
heroku config:set DEBUG=False
# DATABASE_URL auto-set by PostgreSQL addon
```

## Support & Resources

- **Heroku Documentation**: [devcenter.heroku.com](https://devcenter.heroku.com/)
- **Django on Heroku**: [devcenter.heroku.com/articles/django-app-configuration](https://devcenter.heroku.com/articles/django-app-configuration)
- **Heroku Support**: [help.heroku.com](https://help.heroku.com/)
- **OpenAI Documentation**: [platform.openai.com/docs](https://platform.openai.com/docs)

## Quick Reference Commands

```bash
# Deploy
git push heroku main

# View logs
heroku logs --tail

# Run migrations
heroku run python manage.py migrate

# Collect static files
heroku run python manage.py collectstatic --noinput

# Create superuser
heroku run python manage.py createsuperuser

# Open app
heroku open

# Restart
heroku restart

# Check config
heroku config

# Shell access
heroku run python manage.py shell
```

## Next Steps After Deployment

1. **Test thoroughly**: Upload test resumes and verify functionality
2. **Monitor usage**: Check OpenAI API usage and costs
3. **Set up monitoring**: Consider New Relic or other monitoring tools
4. **Configure backups**: Set up automatic database backups
5. **Custom domain**: Add your own domain if desired
6. **Performance tuning**: Optimize as needed based on usage

## Success Checklist

- [ ] Heroku app created
- [ ] PostgreSQL addon added
- [ ] All environment variables set
- [ ] Code pushed to Heroku
- [ ] Database migrations run
- [ ] Static files collected
- [ ] Superuser created (optional)
- [ ] App tested and working
- [ ] Logs monitored
- [ ] OpenAI API key verified
- [ ] Custom domain configured (optional)

Congratulations! Your Resume Sorter app is now live on Heroku! 🎉
