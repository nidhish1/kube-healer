# Borex - Scraping and Enrichment Microservices

A microservices architecture for scraping and enriching lead data using MongoDB.

## Project Structure

```
borex/
├── db-service/          # Database service with DAO layer
├── docker-compose.yml   # Docker Compose configuration
├── Makefile            # Service management commands
└── README.md           # This file
```

## Services

### DB Service (`db-service/`)

A Golang service with database layer for managing scraping targets and leads enrichment using MongoDB.

## Architecture

The service consists of:
- **Database Layer (DAO/DBO)**: Handles all database operations
- **Models**: Data structures for `scrape_targets` and `leads` collections
- **Configuration**: Environment-based configuration management

## Database Structure

### Collection: `scrape_targets`
Stores URLs that need to be scraped.

**Fields:**
- `url`: The URL to scrape
- `status`: "pending", "processing", "completed", "failed"
- `retry_count`: Number of retry attempts
- `started_at`: When processing started
- `completed_at`: When processing completed
- `leads_found`: Count of leads found
- `created_at`, `updated_at`: Timestamps

### Collection: `leads`
Stores people found during scraping.

**Fields:**
- `first_name`, `last_name`: Person's name
- `job_title`: Job title (optional)
- `domain`: Company domain
- `email`: Email address (from Hunter.io)
- `hunter_status`: "ready", "enriched", "not_found", "failed"
- `confidence_score`: Hunter.io confidence score
- `raw_api_response`: Full API response from Hunter.io
- `scrape_target_id`: Reference to the scrape target
- `created_at`, `updated_at`: Timestamps

## Setup

### Prerequisites
- Go 1.21 or higher (for local development)
- MongoDB (local or remote)
- Docker and Docker Compose (for containerized setup)

### Quick Start with Docker (Recommended)

**Using Makefile (Easiest):**
```bash
make start      # Start services in background
make stop       # Stop services
make restart    # Restart services
make logs       # View all logs
make logs-service  # View Go service logs only
make clean      # Stop and remove all data
make help       # Show all available commands
```

**Using Docker Compose directly:**
1. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

2. **Run in detached mode:**
   ```bash
   docker-compose up -d --build
   ```

3. **View logs:**
   ```bash
   docker-compose logs -f borex-service
   ```

4. **Stop services:**
   ```bash
   docker-compose down
   ```

5. **Stop and remove volumes (clean slate):**
   ```bash
   docker-compose down -v
   ```

The Docker setup includes:
- **MongoDB**: Running on port 27017
- **Borex Service**: Connected to MongoDB automatically

### MongoDB Connection (Local Testing)

**Connection String:**
```
mongodb://localhost:27017/borex
```

Use this connection string to connect to MongoDB from:
- MongoDB Compass
- DBeaver
- Any other MongoDB client

**Note:** The `borex` database and collections will appear automatically when data is first inserted.

### Local Development Setup

1. **Navigate to the service directory:**
   ```bash
   cd db-service
   ```

2. **Install dependencies:**
   ```bash
   go mod download
   ```

3. **Set environment variables (optional):**
   ```bash
   export MONGO_URI="mongodb://localhost:27017"
   export DATABASE_NAME="borex"
   ```

   Default values:
   - `MONGO_URI`: `mongodb://localhost:27017`
   - `DATABASE_NAME`: `borex`

4. **Run the service:**
   ```bash
   go run main.go
   ```

## Usage

### ScrapeTargetDAO Operations

```go
ctx := context.Background()
dao := db.NewScrapeTargetDAO()

// Create a new scrape target
target := &models.ScrapeTarget{
    URL: "https://example.com/team",
}
id, err := dao.Create(ctx, target)

// Get and lock a pending target
target, err := dao.GetPending(ctx)

// Update status
err := dao.UpdateStatus(ctx, id, models.StatusCompleted)

// Increment leads found
err := dao.IncrementLeadsFound(ctx, id)

// Reset stuck jobs (run on startup)
count, err := dao.ResetStuckJobs(ctx, 30) // 30 minutes timeout
```

### LeadDAO Operations

```go
ctx := context.Background()
dao := db.NewLeadDAO()

// Create a single lead
lead := &models.Lead{
    FirstName: "John",
    LastName:  "Doe",
    JobTitle:  "Engineer",
    Domain:    "example.com",
    ScrapeTargetID: scrapeTargetID,
}
id, err := dao.Create(ctx, lead)

// Create multiple leads
leads := []*models.Lead{lead1, lead2, lead3}
ids, err := dao.CreateMany(ctx, leads)

// Get leads ready for enrichment
readyLeads, err := dao.GetReady(ctx, 10) // limit 10

// Update Hunter.io enrichment status
confidence := 95
err := dao.UpdateHunterStatus(ctx, id, models.HunterStatusEnriched, 
    "john.doe@example.com", &confidence, rawResponse)
```

## Next Steps

This service provides the database layer. You can now:
1. Create a scraping microservice that uses `ScrapeTargetDAO` and `LeadDAO`
2. Create an enrichment microservice that uses `LeadDAO` for Hunter.io integration
3. Add REST API endpoints if needed
4. Add additional business logic

## DB Service Structure

```
db-service/
├── main.go              # Service entry point
├── go.mod               # Go module file
├── Dockerfile           # Docker image definition
├── .dockerignore        # Docker ignore file
├── config/
│   └── config.go        # Configuration management
├── models/
│   ├── scrape_target.go # ScrapeTarget model
│   └── lead.go          # Lead model
└── db/
    ├── connection.go           # Database connection
    ├── scrape_target_dao.go    # ScrapeTarget DAO
    └── lead_dao.go             # Lead DAO
```

## Adding New Services

To add a new microservice:
1. Create a new folder (e.g., `scraper-service/`, `enrichment-service/`)
2. Add the service to `docker-compose.yml`
3. Update the Makefile if needed

# kube-healer
