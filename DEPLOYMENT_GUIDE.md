# Discord UCL Prediction Bot - Deployment Guide

## Current Issues with Render

Your bot is experiencing downtime issues on Render's free tier due to:
- Resource limitations and automatic spin-down after inactivity
- Unreliable keep-alive mechanisms on free tiers
- Limited CPU and memory allocation

## Recommended Hosting Solutions

### 1. Railway (Recommended) ⭐

**Why Railway:**
- More generous free tier with better uptime
- Easy GitHub integration
- Better resource allocation
- $5/month for reliable hosting

**Setup Steps:**
1. Go to [Railway.app](https://railway.app)
2. Sign up with GitHub
3. Create new project from GitHub repo
4. Add environment variables:
   - `DISCORD_TOKEN`
   - `FIREBASE_PROJECT_ID`
   - `FIREBASE_PRIVATE_KEY_ID`
   - `FIREBASE_PRIVATE_KEY`
   - `FIREBASE_CLIENT_EMAIL`
   - `FIREBASE_CLIENT_ID`
   - `FIREBASE_AUTH_URI`
   - `FIREBASE_TOKEN_URI`
   - `FIREBASE_AUTH_PROVIDER_CERT_URL`
   - `FIREBASE_CLIENT_CERT_URL`
   - `FOOTBALL_API_KEY`
   - `DISCORD_CHANNEL_ID`
5. Deploy automatically

### 2. Heroku

**Why Heroku:**
- More stable than Render's free tier
- Well-established platform
- Good Discord bot support

**Setup Steps:**
1. Install Heroku CLI
2. Create `Procfile`: `worker: python main.py`
3. Deploy: `git push heroku main`
4. Scale: `heroku ps:scale worker=1`

### 3. DigitalOcean App Platform

**Why DigitalOcean:**
- Very reliable hosting
- Good performance
- Reasonable pricing

**Setup Steps:**
1. Create account at DigitalOcean
2. Create new App from GitHub
3. Configure build command: `pip install -r requirements.txt`
4. Set run command: `python main.py`
5. Add environment variables

### 4. VPS Solutions (Most Control)

**Options:**
- DigitalOcean Droplet ($4-6/month)
- Linode ($5/month)
- Vultr ($2.50-6/month)

**Setup Steps:**
1. Create Ubuntu VPS
2. Install Python and dependencies
3. Set up systemd service
4. Configure auto-restart on failure

## Environment Variables Required

Make sure these are set in your hosting platform:

```bash
DISCORD_TOKEN=your_discord_bot_token
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_CERT_URL=your_client_cert_url
FOOTBALL_API_KEY=your_football_api_key
DISCORD_CHANNEL_ID=your_discord_channel_id
```

## Improvements Made to Your Code

### 1. Enhanced Keep-Alive
- Added health check endpoint (`/health`)
- Better error handling
- Daemon thread for Flask server

### 2. Automatic Restart Logic
- Bot automatically restarts on crashes
- 30-second delay between restart attempts
- Proper error logging

### 3. Better Error Handling
- Comprehensive logging throughout the bot
- Error handling for all async operations
- Graceful handling of Discord API errors

### 4. Task Management
- Prevents duplicate task starts
- Better task error handling
- Connection state monitoring

## Migration Steps

1. **Backup your current setup**
   - Export your Firestore data
   - Save your environment variables

2. **Choose a new hosting platform**
   - Railway is recommended for ease of use
   - VPS for maximum control

3. **Deploy to new platform**
   - Follow the specific setup steps above
   - Test thoroughly before switching

4. **Update your bot**
   - The improved code is already in your repository
   - Deploy the updated version

## Monitoring and Maintenance

### Logs
- Check logs regularly for errors
- Monitor bot uptime
- Watch for memory/CPU usage

### Health Checks
- Use the `/health` endpoint for monitoring
- Set up uptime monitoring (UptimeRobot, etc.)

### Backup Strategy
- Regular Firestore exports
- Environment variable backups
- Code repository backups

## Cost Comparison

| Platform | Free Tier | Paid Tier | Reliability |
|----------|-----------|-----------|-------------|
| Render | Limited | $7/month | ⭐⭐ |
| Railway | Good | $5/month | ⭐⭐⭐⭐ |
| Heroku | Limited | $7/month | ⭐⭐⭐ |
| DigitalOcean | None | $5/month | ⭐⭐⭐⭐⭐ |
| VPS | None | $4-6/month | ⭐⭐⭐⭐⭐ |

## Next Steps

1. **Immediate**: Deploy the improved code to your current Render setup
2. **Short-term**: Migrate to Railway or Heroku for better reliability
3. **Long-term**: Consider VPS for maximum control and cost efficiency

The improved code should significantly reduce downtime even on Render's free tier, but migrating to a more reliable platform is the best long-term solution.
