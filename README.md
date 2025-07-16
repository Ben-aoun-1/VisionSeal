# VisionSeal - Enterprise Tender Management Platform

A comprehensive, secure, and intelligent tender management platform designed for African markets. Built with FastAPI and React, featuring AI-powered document analysis, automated web scraping, and enterprise-grade security.

## 🌟 Features

### Core Capabilities
- **🔍 Intelligent Tender Discovery**: Automated scraping from UNGM and TuniPages
- **🤖 AI-Powered Analysis**: RAG-based document analysis and response generation
- **📊 Advanced Analytics**: Real-time dashboards and comprehensive reporting
- **🔐 Enterprise Security**: JWT authentication, rate limiting, and comprehensive validation
- **🌍 African Market Focus**: Optimized for French-speaking African markets

### Technical Excellence
- **Async/Await Architecture**: High-performance async operations throughout
- **Type Safety**: Full TypeScript frontend with comprehensive type definitions
- **Modern UI**: Material-UI with responsive design and dark mode support
- **Scalable Backend**: FastAPI with proper dependency injection and middleware
- **Production Ready**: Comprehensive logging, health checks, and monitoring

## 🏗️ Architecture

### Backend Stack
- **FastAPI**: Modern, fast web framework with automatic OpenAPI documentation
- **SQLAlchemy**: Advanced ORM with async support and connection pooling
- **Supabase**: Cloud-native PostgreSQL with Row Level Security
- **Playwright**: Modern web automation for reliable scraping
- **ChromaDB**: Vector database for AI-powered document retrieval
- **OpenAI**: GPT-4 integration for intelligent document analysis

### Frontend Stack
- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Full type safety with strict compiler settings
- **Material-UI**: Professional component library with theming
- **React Query**: Efficient server state management and caching
- **Vite**: Fast development and optimized production builds

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+ (or use Supabase)
- OpenAI API key

### Installation

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd VisionSeal-Refactored
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   
   Create a `.env` file in the project root:
   ```bash
   # Core Settings
   ENVIRONMENT=development
   SECRET_KEY=your-secret-key-here
   
   # Database
   SUPABASE_URL=your-supabase-url
   SUPABASE_SERVICE_KEY=your-service-key
   
   # AI Integration
   OPENAI_API_KEY=your-openai-api-key
   
   # Scraper Credentials
   UNGM_USERNAME=your-ungm-username
   UNGM_PASSWORD=your-ungm-password
   TUNIPAGES_USERNAME=your-tunipages-username
   TUNIPAGES_PASSWORD=your-tunipages-password
   
   # Frontend
   ALLOWED_ORIGINS=http://localhost:3000
   ```

3. **Database Setup**
   ```bash
   # Run migrations (if using PostgreSQL)
   psql -d your_database -f database/migrations/000_fresh_start.sql
   
   # Or use Supabase and run the SQL in their editor
   ```

4. **Start the Application**
   ```bash
   # Terminal 1: Start backend
   python src/main.py
   
   # Terminal 2: Start frontend
   cd visionseal-frontend
   npm install
   npm run dev
   ```

5. **Access the Application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8080
   - API Documentation: http://localhost:8080/docs

## 📚 Documentation

### API Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user

#### Tenders
- `GET /api/v1/tenders/` - List tenders with filtering and pagination
- `GET /api/v1/tenders/{id}` - Get specific tender
- `GET /api/v1/tenders/stats/summary` - Get tender statistics
- `GET /api/v1/tenders/filters/options` - Get filter options

#### Automation
- `POST /api/v1/automation/start` - Start scraping automation
- `GET /api/v1/automation/status/{source}` - Get automation status
- `GET /api/v1/automation/results/{source}` - Get scraping results

#### AI Processing
- `POST /api/v1/ai/analyze` - Analyze uploaded documents
- `POST /api/v1/ai/generate` - Generate AI responses
- `POST /api/v1/ai/generate-report` - Generate configurable reports
- `POST /api/v1/ai/chat` - Interactive Q&A with documents

#### Direct Scrapers
- `POST /api/v1/scrapers/ungm/start` - Start UNGM scraper
- `POST /api/v1/scrapers/tunipages/start` - Start TuniPages scraper
- `GET /api/v1/scrapers/status` - Get all scraper statuses

### Key Features

#### Intelligent Tender Discovery
- **UNGM Scraper**: Automated extraction from UN Global Marketplace
- **TuniPages Scraper**: Specialized scraper for Tunisian markets
- **Batch Processing**: Efficient AJAX-based pagination
- **Relevance Scoring**: AI-powered relevance calculation
- **Duplicate Detection**: Intelligent deduplication

#### AI-Powered Analysis
- **Document Processing**: Multi-format support (PDF, DOCX, PPTX)
- **RAG System**: Retrieval-Augmented Generation with ChromaDB
- **Response Generation**: Automated proposal generation
- **Configurable Reports**: Brief, detailed, and comprehensive formats
- **Multi-language Support**: French and English processing

#### Security & Performance
- **JWT Authentication**: Secure token-based authentication
- **Rate Limiting**: Prevents abuse with configurable limits
- **Input Validation**: Comprehensive validation and sanitization
- **CORS Protection**: Properly configured cross-origin requests
- **Async Operations**: High-performance async/await throughout

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ENVIRONMENT` | Application environment (development/production) | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_SERVICE_KEY` | Supabase service key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `UNGM_USERNAME` | UNGM login username | Yes |
| `UNGM_PASSWORD` | UNGM login password | Yes |
| `TUNIPAGES_USERNAME` | TuniPages login username | Yes |
| `TUNIPAGES_PASSWORD` | TuniPages login password | Yes |

### Database Schema

The application uses a comprehensive PostgreSQL schema with:
- **Tenders Table**: Core tender information with full-text search
- **Row Level Security**: User-based data access control
- **Automated Triggers**: Search vector updates
- **Optimized Indexes**: Performance-optimized queries

### AI Configuration

- **Chunk Size**: 1500 characters with 200 character overlap
- **Embedding Model**: OpenAI text-embedding-3-large
- **Generation Model**: GPT-4 Turbo
- **Vector Database**: ChromaDB for local storage
- **Context Window**: Optimized for 8k token limit

## 🛠️ Development

### Project Structure
```
VisionSeal-Refactored/
├── src/                     # Main application code
│   ├── api/                 # FastAPI routes and middleware
│   ├── core/                # Core functionality
│   ├── automation/          # Web scraping and automation
│   ├── ai/                  # AI processing and vector storage
│   └── main.py              # Application entry point
├── database/                # Database migrations
├── config/                  # Configuration files
├── data/                    # Data storage
├── visionseal-frontend/     # React frontend
└── requirements.txt         # Python dependencies
```

### Development Commands

```bash
# Backend development
python src/main.py  # Start with auto-reload

# Frontend development
cd visionseal-frontend
npm run dev  # Start development server
npm run build  # Build for production

# Database migrations
psql -d database -f database/migrations/000_fresh_start.sql
```

### Testing

```bash
# Backend tests
python -m pytest tests/

# Frontend tests
cd visionseal-frontend
npm test

# API testing
curl -X GET "http://localhost:8080/health"
```

## 🚀 Production Deployment

### Security Considerations
- Use secure secret management for environment variables
- Enable SSL/TLS for all connections
- Configure proper firewall rules
- Implement monitoring and alerting
- Regular security updates

### Performance Optimization
- Database connection pooling
- Redis caching for frequently accessed data
- CDN for static assets
- Load balancing for high availability
- Monitoring and metrics collection

### Deployment Options

#### Traditional Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Run with production settings
ENVIRONMENT=production python src/main.py
```

#### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "src/main.py"]
```

## 📊 Monitoring and Health Checks

### Health Endpoints
- `/health` - Basic health status
- `/health/detailed` - Comprehensive service status
- `/health/live` - Kubernetes liveness probe
- `/health/ready` - Kubernetes readiness probe

### Metrics
- Request count and latency
- Database connection health
- AI processing performance
- Scraper success rates
- Memory and CPU usage

## 🔒 Security Features

### Authentication & Authorization
- JWT-based authentication with configurable expiration
- Role-based access control (RBAC)
- Session management with timeout
- Secure password hashing with PassLib

### Input Validation
- Comprehensive request validation with Pydantic
- File upload security with type and size validation
- SQL injection prevention
- XSS protection

### Rate Limiting
- Configurable rate limits per endpoint
- IP-based rate limiting
- User-specific rate limits
- Exponential backoff for retries

## 🤖 AI Integration

### Document Processing
- Multi-format support (PDF, DOCX, PPTX)
- OCR integration for scanned documents
- Table extraction and processing
- Metadata extraction and analysis

### RAG System
- ChromaDB vector storage
- OpenAI embeddings (text-embedding-3-large)
- Similarity search with metadata filtering
- Context-aware response generation

### Report Generation
- Configurable report types (proposal, analysis, summary)
- Multiple length options (brief, detailed, comprehensive)
- Tone customization (professional, technical, persuasive)
- Multi-language support (French, English)

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Issues**
   - Check Supabase credentials
   - Verify network connectivity
   - Ensure RLS policies are configured

2. **AI Integration Problems**
   - Verify OpenAI API key
   - Check API rate limits
   - Ensure ChromaDB is accessible

3. **Scraper Authentication Failures**
   - Verify UNGM/TuniPages credentials
   - Check for website changes
   - Review browser automation settings

4. **Frontend Build Issues**
   - Clear node_modules and reinstall
   - Check TypeScript compilation
   - Verify environment variables

### Performance Optimization

1. **Database Performance**
   - Enable connection pooling
   - Optimize query indexes
   - Use database monitoring tools

2. **API Performance**
   - Implement response caching
   - Use async/await consistently
   - Monitor memory usage

3. **Frontend Performance**
   - Implement code splitting
   - Use React.memo for expensive components
   - Optimize image loading

## 📄 License

This project is proprietary software developed for Topaza International.

## 🤝 Contributing

For internal development:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
5. Ensure all tests pass

## 📞 Support

For technical support and questions:
- Create an issue in the repository
- Contact the development team
- Review the comprehensive documentation

---

**VisionSeal** - Empowering African businesses with intelligent tender management.