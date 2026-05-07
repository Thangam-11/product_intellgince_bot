# 🤖 Customer Product Intelligence Bot

> An AI-powered e-commerce product intelligence system using RAG (Retrieval-Augmented Generation) — fully automated from code push to production on AWS.

<img width="1596" height="727" alt="WhatsApp Image 2026-05-07 at 3 45 24 PM" src="https://github.com/user-attachments/assets/a3e1c367-47aa-44a3-aa5d-6bb5fd78390c" />

# problem Statement 

<img width="1591" height="916" alt="WhatsApp Image 2026-05-07 at 3 46 12 PM" src="https://github.com/user-attachments/assets/75bde84e-d54a-4720-a2b2-21db3736e308" />



## 📖 About This Project

The **Customer Product Intelligence Bot** is a production-grade RAG system that answers product questions based on real customer reviews — no hallucinations, just grounded answers from actual data.

Ask questions like:
- *"Are boAt headphones good for bass?"*
- *"Compare boAt BassHeads 100 vs 225"*
- *"Best budget headphones under ₹500?"*

The bot retrieves relevant reviews from a vector database and generates accurate, context-aware answers using a Large Language Model.

> 🎯 **Key Difference:** Answers are grounded in real customer reviews stored in AstraDB — not hallucinated responses.

---

## 🎓 What You'll Learn

- Building a **production RAG pipeline** from scratch
- **FastAPI** backend with async support and middleware
- **Vector database** integration with AstraDB
- **AWS ECS Fargate** deployment with zero manual steps
- **CI/CD pipeline** with GitHub Actions
- **Secrets management** with AWS SSM Parameter Store
- **Docker** containerization and ECR image management

---


<img width="1536" height="1024" alt="ChatGPT Image Apr 28, 2026, 12_58_56 PM" src="https://github.com/user-attachments/assets/6b93bdc4-b6eb-4957-bf4f-6333bf892063" />


# Local Architecture Components

## Frontend
- HTML
- CSS
- JavaScript
- Static file serving using Nginx

## Backend
- FastAPI
- REST APIs
- Request validation
- AI inference handling

## RAG Pipeline
- LangChain orchestration
- Query understanding
- Retrieval workflow
- Context augmentation
- Response generation

## Vector Database
- AstraDB
- Semantic search
- Document embeddings
- Context retrieval

## LLM & Embedding Models
- OpenRouter LLM APIs
- Google Gemini embedding models

## Containerization
- Docker
- Docker Compose

---

<img width="1290" height="887" alt="image" src="https://github.com/user-attachments/assets/87d0cffc-480c-4129-aa16-084e4b6b214c" />

# Cloud Architecture Overview (AWS)

The cloud deployment architecture is designed for scalable and production-ready deployment using AWS services.

The deployment pipeline automates:
- Docker image creation
- Container registry management
- ECS deployment
- Cloud infrastructure integration



<img width="1300" height="887" alt="image" src="https://github.com/user-attachments/assets/cce36227-2a92-4e22-bfc5-71e134ef5b0b" />

# AWS Services Used

## Amazon ECS
Container orchestration and deployment

## Amazon ECR
Docker image registry

## Application Load Balancer
Traffic routing and scalability

## Amazon S3
Document and artifact storage

## AWS IAM
Access management and permissions

## AWS CloudWatch
Monitoring and logging

<img width="1402" height="505" alt="image" src="https://github.com/user-attachments/assets/e6d79d00-8dad-477f-91ed-30d4f67f3be4" />


# Cloud Deployment Workflow

1. Developer pushes code to GitHub repository
2. GitHub Actions triggers CI/CD workflow
3. Docker image is built automatically
4. Image is pushed to AWS ECR
5. AWS ECS deploys updated containers
6. Application becomes accessible through Load Balancer
7. AI services communicate with AstraDB and OpenRouter APIs

### CI/CD Pipeline
<img width="1881" height="836" alt="ChatGPT Image Apr 28, 2026, 01_00_48 PM" src="https://github.com/user-attachments/assets/adc35863-5481-4dab-88c7-4fbdacb85ed5" />
 │
     
## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM** | LLaMA 3 8B via OpenRouter | Response generation |
| **Embeddings** | Gemini Embedding | Text vectorization |
| **Vector DB** | AstraDB | Review storage & retrieval |
| **Backend** | FastAPI + Uvicorn | REST API |
| **Frontend** | Vanilla JS + HTML | Chat UI |
| **Container** | Docker | App packaging |
| **Registry** | AWS ECR | Image storage |
| **Deployment** | AWS ECS Fargate | Serverless containers |
| **Secrets** | AWS SSM Parameter Store | Secure config |
| **Logs** | AWS CloudWatch | Monitoring |
| **CI/CD** | GitHub Actions | Automation |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker Desktop
- AWS CLI configured
- AstraDB account
- OpenRouter API key
- Gemini API key

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/customer_product_intelligence-bot
cd customer_product_intelligence-bot

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run the app
uvicorn src.rag_app.main:app --reload --port 8000

# 6. Visit the app
open http://localhost:8000
```

### Environment Variables

```env
GEMINI_API_KEY=your_gemini_api_key
OPEN_ROUTER_API_KEY=your_openrouter_key
ASTRA_DB_API_ENDPOINT=your_astra_endpoint
ASTRA_DB_APPLICATION_TOKEN=your_astra_token
ASTRA_DB_KEYSPACE=default_keyspace
ASTRA_DB_COLLECTION=ecommercedatanew
API_KEY=your_api_key
```

---

## ☁️ AWS Deployment

### Infrastructure Setup

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name product_cluster --region us-east-1

# Create ECR repository
aws ecr create-repository --repository-name product_intelligence_bot --region us-east-1

# Add SSM parameters
aws ssm put-parameter --name GEMINI_API_KEY --type SecureString --value "your_key"
aws ssm put-parameter --name OPEN_ROUTER_API_KEY --type SecureString --value "your_key"
aws ssm put-parameter --name ASTRA_DB_API_ENDPOINT --type SecureString --value "your_endpoint"
aws ssm put-parameter --name ASTRA_DB_APPLICATION_TOKEN --type SecureString --value "your_token"
aws ssm put-parameter --name ASTRA_DB_KEYSPACE --type SecureString --value "default_keyspace"
aws ssm put-parameter --name ASTRA_DB_COLLECTION --type SecureString --value "ecommercedatanew"
aws ssm put-parameter --name API_KEY --type SecureString --value "your_api_key"
```

### GitHub Secrets Required

Add these in **Settings → Secrets → Actions**:

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |

### Automated Deployment

Every push to `main` triggers the full CI/CD pipeline:

1. ✅ **CI** — runs tests with pytest
2. 🐳 **Build** — builds Docker image
3. 📦 **Push** — pushes to AWS ECR
4. 📋 **Register** — creates new task definition with SSM secrets
5. 🚀 **Deploy** — updates ECS Fargate service
6. 🔍 **Smoke test** — verifies `/health` endpoint

---

## 📡 API Reference

### Health Check
```bash
GET /health
```
```json
{"status": "ok", "environment": "production", "uptime_seconds": 1234}
```

### Chat
```bash
POST /chat
Headers: X-API-Key: your_api_key
Content-Type: application/json

{
  "msg": "Are boAt headphones good for bass?"
}
```
```json
{
  "response": "Based on customer reviews, boAt headphones are highly praised for bass quality...",
  "request_id": "abc123",
  "cached": false
}
```

### Interactive Docs
```
http://your-ip:8000/docs
```

---

## 🗂️ Project Structure

```
customer_product_intelligence-bot/
├── src/
│   └── rag_app/
│       ├── api/              # API routes and endpoints
│       ├── configure/        # Settings and configuration
│       ├── core_app/         # RAG chain and retrieval logic
│       └── main.py           # FastAPI app entry point
├── templates/
│   └── chat.html             # Frontend chat UI
├── static/                   # Static assets
├── tests/                    # Test suite
├── .github/
│   └── workflows/
│       ├── ci.yml            # CI pipeline
│       └── cd.yml            # CD pipeline
├── Dockerfile                # Container definition
├── requirements.txt          # Python dependencies
└── README.md
```

---

## 🔧 CI/CD Pipeline Details

### CI Pipeline (`ci.yml`)
- Triggered on every push to `main`
- Runs pytest test suite
- Linting and code quality checks

### CD Pipeline (`cd.yml`)
- Triggered when CI passes
- Builds and pushes Docker image to ECR with git SHA tag
- Registers new ECS task definition with SSM secrets injected
- Auto-creates service if it doesn't exist, updates if it does
- Waits for service stability
- Runs smoke test against `/health` endpoint

---

## 💡 Key Design Decisions

- **SSM over hardcoded secrets** — All sensitive config pulled from AWS SSM at runtime
- **Immutable image tags** — Every deploy uses `github.sha` tag for traceability
- **Graceful Redis fallback** — App runs without Redis, just without semantic caching
- **API key auth** — All chat endpoints protected with `X-API-Key` header
- **Production docs** — Swagger UI available at `/docs` for easy testing

---

## 🧹 Cleanup (Avoid AWS Costs)

```bash
# Scale down service
aws ecs update-service --cluster product_cluster --service product-service --desired-count 0

# Delete service
aws ecs delete-service --cluster product_cluster --service product-service --force

# Delete cluster
aws ecs delete-cluster --cluster product_cluster

# Delete ECR repo
aws ecr delete-repository --repository-name product_intelligence_bot --force

# Delete SSM params
aws ssm delete-parameters --names GEMINI_API_KEY OPEN_ROUTER_API_KEY ASTRA_DB_API_ENDPOINT ASTRA_DB_APPLICATION_TOKEN ASTRA_DB_KEYSPACE ASTRA_DB_COLLECTION API_KEY
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) file for details.

---

<div align="center">

 Author

Thangarasu M

AI/ML Engineer | MLOps Enthusiast | Generative AI Developer
  Built with ❤️ using FastAPI, AstraDB, AWS ECS, and GitHub Actions
</div>
