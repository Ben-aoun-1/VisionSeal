#!/bin/bash
# VisionSeal FREE Deployment Script

set -e

echo "🆓 VisionSeal FREE Deployment Options"
echo "====================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[FREE]${NC} $1"
}

echo ""
echo "💸 Choose your FREE deployment option:"
echo "1) Railway (Recommended - $5/month credit = FREE)"
echo "2) Render (Free tier with sleep mode)"
echo "3) Fly.io (Free allowances)"
echo "4) Oracle Cloud Always Free (Advanced)"
echo "5) Local + Ngrok (Testing only)"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        print_warning "Railway FREE Deployment"
        echo ""
        print_info "Railway gives you $5/month credit - enough to run VisionSeal for FREE!"
        
        # Check if Railway CLI is installed
        if ! command -v railway &> /dev/null; then
            print_info "Installing Railway CLI..."
            npm install -g @railway/cli
        fi
        
        print_info "Railway deployment steps:"
        echo "1. Run: railway login"
        echo "2. Run: railway init"
        echo "3. Add environment variables:"
        echo "   railway variables set SECRET_KEY=your-secret-key"
        echo "   railway variables set SUPABASE_URL=your-supabase-url"
        echo "   railway variables set SUPABASE_ANON_KEY=your-anon-key"
        echo "   railway variables set SUPABASE_SERVICE_KEY=your-service-key"
        echo "4. Run: railway up"
        echo ""
        print_success "Cost: FREE (covered by $5 monthly credit)"
        print_success "Features: No sleep mode, automatic deployments, custom domains"
        ;;
        
    2)
        print_warning "Render FREE Deployment"
        echo ""
        print_info "Render offers 750 hours/month FREE (enough for 24/7)"
        print_warning "Note: App sleeps after 15min inactivity (wakes when accessed)"
        
        print_info "Render deployment steps:"
        echo "1. Go to https://render.com and sign up (FREE)"
        echo "2. Connect your GitHub repository"
        echo "3. Create new Web Service"
        echo "4. Use these settings:"
        echo "   - Build Command: pip install -r requirements-production.txt && playwright install chromium"
        echo "   - Start Command: uvicorn src.main:app --host 0.0.0.0 --port \$PORT"
        echo "5. Add environment variables in Render dashboard"
        echo ""
        print_success "Cost: 100% FREE"
        print_warning "Limitation: 15min sleep time (acceptable for most use cases)"
        ;;
        
    3)
        print_warning "Fly.io FREE Deployment"
        echo ""
        print_info "Fly.io gives $5/month credit + 3 shared VMs FREE"
        
        # Check if flyctl is installed
        if ! command -v flyctl &> /dev/null; then
            print_info "Installing Fly CLI..."
            curl -L https://fly.io/install.sh | sh
        fi
        
        print_info "Fly.io deployment steps:"
        echo "1. Run: flyctl auth login"
        echo "2. Run: flyctl launch --no-deploy"
        echo "3. Set secrets (FREE tier):"
        echo "   flyctl secrets set SECRET_KEY=your-secret"
        echo "   flyctl secrets set SUPABASE_URL=your-url"
        echo "4. Run: flyctl deploy"
        echo ""
        print_success "Cost: FREE (covered by credits + free VMs)"
        print_success "Features: Global edge deployment, excellent performance"
        ;;
        
    4)
        print_warning "Oracle Cloud Always Free (Advanced Users)"
        echo ""
        print_info "Oracle Cloud offers PERMANENT free hosting (not trial)"
        print_warning "Requires more technical setup but completely free forever"
        
        print_info "Oracle Cloud setup:"
        echo "1. Sign up at oracle.com/cloud/free"
        echo "2. Create VM instance (1GB RAM, 200GB storage)"
        echo "3. Install Docker:"
        echo "   sudo apt update && sudo apt install docker.io docker-compose"
        echo "4. Clone repository and deploy:"
        echo "   git clone <your-repo>"
        echo "   cd VisionSeal-Refactored"
        echo "   docker-compose up -d"
        echo ""
        print_success "Cost: FREE FOREVER"
        print_success "Resources: 1GB RAM, 200GB storage, 10TB bandwidth"
        print_warning "Effort: High (manual server setup required)"
        ;;
        
    5)
        print_warning "Local + Ngrok (Testing Only)"
        echo ""
        print_info "Run VisionSeal locally and expose to internet for FREE"
        
        print_info "Local + Ngrok setup:"
        echo "1. Start VisionSeal locally:"
        echo "   uvicorn src.main:app --host 0.0.0.0 --port 8080"
        echo "2. In another terminal, expose to internet:"
        echo "   npx ngrok http 8080"
        echo "3. Use the ngrok URL to access your app from anywhere"
        echo ""
        print_success "Cost: 100% FREE"
        print_warning "Best for: Testing, development, demos"
        print_warning "Not for: Production use (URL changes each restart)"
        ;;
        
    *)
        echo "Invalid choice!"
        exit 1
        ;;
esac

echo ""
print_success "FREE deployment option selected!"
print_info "Remember to:"
echo "  📋 Set all environment variables from .env"
echo "  🔒 Use placeholders in .env (keep real credentials secure)"
echo "  🧪 Test thoroughly after deployment"
echo "  📊 Monitor usage to stay within free limits"
echo ""

print_info "Need help? Check FREE_DEPLOYMENT.md for detailed instructions"

# Show current environment variables that need to be set
echo ""
print_info "Environment variables you'll need to set:"
echo "  SECRET_KEY=your-secret-key-min-32-chars"
echo "  SUPABASE_URL=your-supabase-url"
echo "  SUPABASE_ANON_KEY=your-anon-key"
echo "  SUPABASE_SERVICE_KEY=your-service-key"
echo "  UNGM_USERNAME=your-ungm-username"
echo "  UNGM_PASSWORD=your-ungm-password"
echo "  TUNIPAGES_USERNAME=your-tunipages-username"
echo "  TUNIPAGES_PASSWORD=your-tunipages-password"
echo ""
print_success "VisionSeal can run completely FREE! 🎉"