# 🚀 VisionSeal Deployment Guide

## 📋 Pre-Deployment Checklist

Before deploying VisionSeal to production, ensure you have:

- ✅ **Security audit passed** (`python3 security_check.py`)
- ✅ **Environment variables configured** (copy `.env.example` to `.env`)
- ✅ **Supabase database set up** with proper tables and RLS policies
- ✅ **API keys obtained** (OpenAI, UNGM credentials, etc.)
- ✅ **Domain name ready** (optional but recommended)

## 🎯 Quick Start

Run the automated deployment script:

```bash
./deploy.sh
```

This will guide you through platform-specific deployment options.

## 🐳 Option 1: Docker Compose (Recommended for VPS)

### Requirements
- Linux server with Docker and Docker Compose
- 2GB+ RAM, 20GB+ storage
- Domain name (optional)

### Steps

1. **Clone and configure**:
```bash
git clone <your-repo>
cd VisionSeal-Refactored
cp .env.example .env
# Edit .env with your credentials
```

2. **Deploy**:
```bash
docker-compose up -d
```

3. **Access**:
- Application: `http://your-server-ip`
- API docs: `http://your-server-ip/api/docs`

### Production Optimizations

**Enable SSL** (recommended):
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Update nginx.conf to enable HTTPS section
```

**Monitor logs**:
```bash
docker-compose logs -f visionseal
```

## 🚄 Option 2: Railway (Easiest)

### Why Railway?
- ✅ **Automatic deployments** from Git
- ✅ **Built-in database** options
- ✅ **Generous free tier**
- ✅ **Zero DevOps** required

### Steps

1. **Install Railway CLI**:
```bash
npm install -g @railway/cli
railway login
```

2. **Deploy**:
```bash
railway init
railway up
```

3. **Configure environment**:
- Go to Railway dashboard
- Add all variables from `.env`
- Deploy with `railway up`

**Estimated cost**: $5-20/month depending on usage

## ✈️ Option 3: Fly.io (Best for Production)

### Why Fly.io?
- ✅ **Global edge deployment**
- ✅ **Excellent performance**
- ✅ **Docker-native**
- ✅ **Reasonable pricing**

### Steps

1. **Install Fly CLI**:
```bash
curl -L https://fly.io/install.sh | sh
flyctl auth login
```

2. **Launch app**:
```bash
flyctl launch --no-deploy
```

3. **Set secrets**:
```bash
flyctl secrets set SECRET_KEY="your-secret-key"
flyctl secrets set SUPABASE_URL="your-supabase-url"
flyctl secrets set SUPABASE_ANON_KEY="your-anon-key"
flyctl secrets set SUPABASE_SERVICE_KEY="your-service-key"
flyctl secrets set OPENAI_API_KEY="your-openai-key"
flyctl secrets set UNGM_USERNAME="your-ungm-username"
flyctl secrets set UNGM_PASSWORD="your-ungm-password"
flyctl secrets set TUNIPAGES_USERNAME="your-tunipages-username"
flyctl secrets set TUNIPAGES_PASSWORD="your-tunipages-password"
```

4. **Deploy**:
```bash
flyctl deploy
```

**Estimated cost**: $10-30/month depending on usage

## ☁️ Option 4: Vercel (Serverless)

### ⚠️ Limitations
- **Browser automation may not work** (serverless limitations)
- **Good for frontend + API**, not for scraping
- **Consider this for dashboard only**

### Steps

1. **Install Vercel CLI**:
```bash
npm install -g vercel
vercel login
```

2. **Deploy**:
```bash
vercel --prod
```

3. **Configure**:
- Add environment variables in Vercel dashboard
- May need external scraping service

## 🔧 Option 5: Manual VPS Setup

### Requirements
- Ubuntu 20.04+ server
- 2GB+ RAM, 20GB+ storage
- Root or sudo access

### Full Setup Script

```bash
#!/bin/bash
# Ubuntu VPS setup

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-pip nginx certbot python3-certbot-nginx

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose-plugin

# Clone repository
git clone <your-repo>
cd VisionSeal-Refactored

# Configure environment
cp .env.example .env
nano .env  # Edit with your credentials

# Install Python dependencies
pip3 install -r requirements-production.txt

# Install Playwright
playwright install chromium
sudo playwright install-deps

# Configure Nginx
sudo cp nginx.conf /etc/nginx/sites-available/visionseal
sudo ln -s /etc/nginx/sites-available/visionseal /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Create systemd service
sudo tee /etc/systemd/system/visionseal.service > /dev/null <<EOF
[Unit]
Description=VisionSeal API
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/path/to/VisionSeal-Refactored
ExecStart=/usr/bin/python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable visionseal
sudo systemctl start visionseal

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Check status
sudo systemctl status visionseal
```

## 🔐 Environment Variables

Ensure these are set in your deployment platform:

### Required
```bash
SECRET_KEY=your-secure-secret-key-min-32-chars
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
```

### Optional but Recommended
```bash
ENVIRONMENT=production
DEBUG=false
OPENAI_API_KEY=your-openai-key
UNGM_USERNAME=your-ungm-username
UNGM_PASSWORD=your-ungm-password
TUNIPAGES_USERNAME=your-tunipages-username
TUNIPAGES_PASSWORD=your-tunipages-password
```

## 📊 Monitoring & Maintenance

### Health Checks

All deployments include health check endpoint:
```
GET /health
```

### Logs

**Docker Compose**:
```bash
docker-compose logs -f visionseal
```

**Railway**:
- Check logs in Railway dashboard

**Fly.io**:
```bash
flyctl logs
```

### Performance Monitoring

Monitor these metrics:
- **Response time** (should be <2s)
- **Memory usage** (should be <1GB)
- **CPU usage** (should be <80%)
- **Scraping success rate** (should be >90%)

### Automated Backups

Set up automated database backups:
- **Supabase**: Built-in backups
- **Additional**: Export data weekly

## 🚨 Troubleshooting

### Common Issues

**1. Browser automation fails**:
```bash
# Install missing dependencies
sudo playwright install-deps
```

**2. Permission denied**:
```bash
# Fix file permissions
chmod +x *.py
chmod 600 .env
```

**3. Memory issues**:
```bash
# Increase server memory or optimize scraping
# Reduce concurrent scrapers
```

**4. SSL certificate issues**:
```bash
# Renew certificate
sudo certbot renew
```

### Debug Mode

Enable debug logging:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
```

## 💰 Cost Estimates

| Platform | Free Tier | Paid Plans | Best For |
|----------|-----------|------------|----------|
| Railway | $5/month credit | $5-20/month | Beginners |
| Fly.io | $5/month credit | $10-30/month | Production |
| VPS | None | $5-50/month | Full control |
| Vercel | Generous | $20+/month | Frontend only |

## 🔄 CI/CD Pipeline

The included GitHub Actions workflow automatically:

1. **Tests** security and functionality
2. **Builds** Docker image
3. **Deploys** to Railway (main branch) or Fly.io (production branch)

### Setup CI/CD

1. **Add secrets** to GitHub repository:
   - `RAILWAY_TOKEN` or `FLY_API_TOKEN`
   - All environment variables

2. **Push to main** branch for automatic deployment

## 📞 Support

If you encounter issues:

1. **Check logs** first
2. **Review security check** output
3. **Verify environment variables**
4. **Test locally** with Docker

## 🎉 Post-Deployment

After successful deployment:

1. ✅ **Test authentication** flow
2. ✅ **Verify scraping** functionality
3. ✅ **Check data** in Supabase
4. ✅ **Monitor performance**
5. ✅ **Set up alerts**
6. ✅ **Plan backups**

**Congratulations! VisionSeal is now live! 🚀**