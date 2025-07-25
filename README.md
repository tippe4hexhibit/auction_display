# Auction Display - Generation 2

A real-time web application for managing and displaying auction proceedings, designed for art student auctions and similar educational events.

## Features

- **Real-time auction management** with WebSocket updates
- **Multi-user interface** for administrators, auctioneers, and public viewers
- **Excel data import/export** for sale programs and buyer lists
- **Bidder registration** and lot progression tracking
- **Image upload** support for auction items
- **JWT authentication** for administrative functions

## Architecture

- **Backend**: FastAPI with SQLAlchemy ORM and SQLite database
- **Frontend**: Svelte SPA with real-time WebSocket integration
- **Database**: SQLite with automatic initialization
- **Authentication**: JWT-based with bcrypt password hashing

## Docker Deployment

### Prerequisites

- Docker and Docker Compose installed
- Git for cloning the repository

### Quick Start with Docker Compose

1. **Clone the repository**:
   ```bash
   git clone https://github.com/tippe4hexhibit/auction_display.git
   cd auction_display
   ```

2. **Create data directory**:
   ```bash
   mkdir -p data
   ```

3. **Start the application**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - **API/Backend**: http://localhost:8000
   - **Frontend**: http://localhost:8000 (served by FastAPI)
   - **API Documentation**: http://localhost:8000/docs

### Development Mode

For frontend development with hot-reload:

```bash
# Start both backend and frontend dev server
docker-compose --profile dev up -d

# Frontend dev server will be available at http://localhost:5173
# Backend API remains at http://localhost:8000
```

### Building the Docker Image

1. **Build locally**:
   ```bash
   docker build -t auction-display .
   ```

2. **Tag for DockerHub**:
   ```bash
   docker tag auction-display your-dockerhub-username/auction-display:latest
   ```

3. **Push to DockerHub**:
   ```bash
   docker push your-dockerhub-username/auction-display:latest
   ```

### Using Pre-built Image from DockerHub

Update `docker-compose.yml` to use a pre-built image:

```yaml
services:
  auction-app:
    image: your-dockerhub-username/auction-display:latest
    # Remove the 'build: .' line
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///./data/auction.db
      - SECRET_KEY=your-secret-key-change-in-production
```

### Configuration

#### Environment Variables

- `DATABASE_URL`: Database connection string (default: `sqlite:///./data/auction.db`)
- `SECRET_KEY`: JWT signing key (change in production!)
- `VITE_API_BASE`: Frontend API base URL (for development)

#### Data Persistence

The application data is stored in the `./data` directory, which is mounted as a volume in the container. This ensures:

- **Database persistence** across container restarts
- **Image uploads** are preserved
- **Easy backup** by copying the data directory

#### Port Configuration

- **8000**: FastAPI backend and production frontend
- **5173**: Vite development server (development mode only)

### Production Deployment

1. **Set a secure secret key**:
   ```bash
   # Generate a secure secret key
   openssl rand -hex 32
   ```

2. **Update docker-compose.yml**:
   ```yaml
   environment:
     - SECRET_KEY=your-generated-secure-key-here
   ```

3. **Deploy**:
   ```bash
   docker-compose up -d
   ```

4. **Monitor logs**:
   ```bash
   docker-compose logs -f auction-app
   ```

### Backup and Restore

#### Backup
```bash
# Stop the application
docker-compose down

# Backup data directory
tar -czf auction-backup-$(date +%Y%m%d).tar.gz data/

# Restart application
docker-compose up -d
```

#### Restore
```bash
# Stop the application
docker-compose down

# Restore data directory
tar -xzf auction-backup-YYYYMMDD.tar.gz

# Restart application
docker-compose up -d
```

## Local Development (Non-Docker)

### Prerequisites

- Python 3.12+
- Node.js 18+
- npm or yarn

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend server**:
   ```bash
   python main.py
   ```

   The FastAPI server will start on http://localhost:8000

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Start the development server**:
   ```bash
   npm run dev
   ```

   The Svelte development server will start on http://localhost:5173

### Default Admin Account

- **Username**: `admin`
- **Password**: `admin123`

*Change these credentials immediately in production!*

## API Documentation

When the backend is running, visit http://localhost:8000/docs for interactive API documentation powered by FastAPI's automatic OpenAPI generation.

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000 and 5173 are not in use by other applications
2. **Permission errors**: Check that the data directory is writable
3. **Database issues**: Delete `data/auction.db` to reset the database (will lose all data)
4. **Frontend not loading**: Verify the backend is running and accessible

### Docker Issues

1. **Build failures**: Ensure Docker has sufficient memory allocated
2. **Volume mounting**: Verify the data directory exists and has proper permissions
3. **Network issues**: Check that Docker can access the internet for package downloads

### Getting Help

1. Check the application logs: `docker-compose logs auction-app`
2. Verify container status: `docker-compose ps`
3. Test API connectivity: `curl http://localhost:8000/api/state`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
