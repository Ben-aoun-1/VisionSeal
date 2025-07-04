#!/bin/bash
# VisionSeal Deployment Script

set -e

echo "🚀 VisionSeal Deployment Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_warning "Please copy .env.example to .env and configure your credentials"
    exit 1
fi

# Run security check
print_status "Running security validation..."
if python3 security_check.py; then
    print_success "Security check passed!"
else
    print_error "Security check failed! Please fix issues before deployment"
    exit 1
fi

# Deployment options
echo ""
echo "📦 Choose deployment platform:"
echo "1) Docker Compose (Local/VPS)"
echo "2) Railway (Recommended for beginners)"
echo "3) Fly.io (Recommended for production)"
echo "4) Vercel (Serverless)"
echo "5) Manual setup guide"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        print_status "Deploying with Docker Compose..."
        
        # Check if Docker is installed
        if ! command -v docker &> /dev/null; then
            print_error "Docker is not installed!"
            print_warning "Please install Docker and Docker Compose first"
            exit 1
        fi
        
        # Build and start services
        print_status "Building Docker images..."
        docker-compose build
        
        print_status "Starting services..."
        docker-compose up -d
        
        print_success "Deployment complete!"
        print_status "Access your application at: http://localhost"
        print_status "API docs available at: http://localhost/api/docs"
        ;;
        
    2)
        print_status "Preparing Railway deployment..."
        
        # Check if Railway CLI is installed
        if ! command -v railway &> /dev/null; then
            print_warning "Railway CLI not found. Installing..."
            npm install -g @railway/cli
        fi
        
        print_status "Railway deployment steps:"
        echo "1. Run: railway login"
        echo "2. Run: railway init"
        echo "3. Add environment variables in Railway dashboard"
        echo "4. Run: railway up"
        print_warning "Make sure to set all environment variables from .env in Railway dashboard"
        ;;
        
    3)
        print_status "Preparing Fly.io deployment..."
        
        # Check if flyctl is installed
        if ! command -v flyctl &> /dev/null; then
            print_warning "Fly CLI not found. Please install it:"
            echo "curl -L https://fly.io/install.sh | sh"
            exit 1
        fi
        
        print_status "Fly.io deployment steps:"
        echo "1. Run: flyctl auth login"
        echo "2. Run: flyctl launch --no-deploy"
        echo "3. Set secrets: flyctl secrets set SECRET_KEY=your-secret"
        echo "4. Run: flyctl deploy"
        print_warning "Make sure to set all environment variables as secrets"
        ;;
        
    4)
        print_status "Preparing Vercel deployment..."
        
        print_warning "Note: Vercel has limitations for web scraping due to serverless nature"
        print_status "Vercel deployment steps:"
        echo "1. Install Vercel CLI: npm install -g vercel"
        echo "2. Run: vercel login"
        echo "3. Run: vercel --prod"
        echo "4. Set environment variables in Vercel dashboard"
        ;;
        
    5)
        print_status "Manual setup guide:"
        echo ""
        echo "🔧 VPS/Server Setup:"
        echo "1. Install Python 3.11+, Docker, Nginx"
        echo "2. Clone repository to server"
        echo "3. Copy .env.example to .env and configure"
        echo "4. Install dependencies: pip install -r requirements-production.txt"
        echo "5. Install Playwright: playwright install chromium"
        echo "6. Configure Nginx (use provided nginx.conf)"
        echo "7. Set up SSL certificate (Let's Encrypt recommended)"
        echo "8. Start application: uvicorn src.main:app --host 0.0.0.0 --port 8080"
        echo ""
        echo "🔧 Cloud Platform Setup:"
        echo "1. Upload code to platform"
        echo "2. Configure environment variables"
        echo "3. Set build command: pip install -r requirements-production.txt"
        echo "4. Set start command: uvicorn src.main:app --host 0.0.0.0 --port \$PORT"
        ;;
        
    *)
        print_error "Invalid choice!"
        exit 1
        ;;
esac

echo ""
print_success "Deployment preparation complete!"
print_status "Remember to:"
echo "  ✅ Set all environment variables"
echo "  ✅ Configure domain and SSL"
echo "  ✅ Test all scraping functionality"
echo "  ✅ Monitor application logs"
echo ""
print_status "Need help? Check DEPLOYMENT.md for detailed instructions"