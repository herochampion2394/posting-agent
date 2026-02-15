# Posting Agent - AI Social Media Automation

An AI-powered social media automation platform that helps you create and schedule posts for Twitter and TikTok.

## Features

- 🤖 AI-powered content generation using GPT-4
- 📅 Automatic post scheduling with customizable frequencies
- 🔗 Twitter and TikTok integration
- 📚 Knowledge base for contextual content
- 📊 Trending topics integration
- 📱 Beautiful responsive dashboard

## Tech Stack

### Backend
- FastAPI (Python)
- PostgreSQL
- SQLAlchemy ORM
- OpenAI API
- Twitter API v2 (Tweepy)
- TikTok Content Posting API
- APScheduler for automation

### Frontend
- React 18
- Vite
- React Router
- TanStack Query
- Axios

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL database
- OpenAI API key
- Twitter Developer Account
- TikTok Developer Account

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. Run the server:
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Posts
- `GET /api/posts` - List all posts
- `POST /api/posts` - Create post
- `POST /api/posts/generate` - Generate AI content
- `DELETE /api/posts/{id}` - Delete post

### Schedules
- `GET /api/schedules` - List schedules
- `POST /api/schedules` - Create schedule
- `PUT /api/schedules/{id}/toggle` - Toggle schedule
- `DELETE /api/schedules/{id}` - Delete schedule

### Social Accounts
- `GET /api/social` - List connected accounts
- `GET /api/social/twitter/auth-url` - Get Twitter OAuth URL
- `POST /api/social/twitter/callback` - Twitter OAuth callback
- `GET /api/social/tiktok/auth-url` - Get TikTok OAuth URL
- `POST /api/social/tiktok/callback` - TikTok OAuth callback

### Knowledge Base
- `GET /api/knowledge` - List knowledge documents
- `POST /api/knowledge` - Add document
- `DELETE /api/knowledge/{id}` - Delete document

## How It Works

1. **Connect Social Accounts**: Link your Twitter and TikTok accounts via OAuth
2. **Add Knowledge Base**: Upload documents, articles, or information for context
3. **Create Schedules**: Set posting frequency (daily, weekly, hourly)
4. **AI Generation**: The system automatically generates content using:
   - Your knowledge base
   - Trending topics from the internet
   - Custom prompts/templates
5. **Automatic Posting**: Posts are published according to your schedule

## Database Schema

- `users` - User accounts
- `social_accounts` - Connected Twitter/TikTok accounts
- `posts` - All posts (drafts, scheduled, published)
- `schedules` - Posting schedules
- `knowledge_docs` - Knowledge base documents
- `trending_topics` - Scraped trending data

## Environment Variables

```env
DATABASE_URL=postgresql://user:pass@host:port/dbname
SECRET_KEY=your-jwt-secret
OPENAI_API_KEY=sk-...
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...
```

## Contributing

Feel free to submit issues and pull requests.

## License

MIT License
