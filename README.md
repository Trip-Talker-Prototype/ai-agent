# AI-Agent-GOGO

This repository is a working space for our product that simplify airplane ticketing with AI (by prompt or voices). In this README.md will explain how to install and run this program.

## Install Packages
### 1. Install uv
Uv is a fast, and reliable python packages installer. it will help us to managing our packages

First install uv <br> 
`curl -LsSf https://astral.sh/uv/install.sh | sh` <br>

In case you don't have cURL<br>
`wget -qO- https://astral.sh/uv/install.sh | sh`

### 2. Create Virtual Environment
Making packages more maintainable, we can install venv(virtual environment) for our projects. Installing packages from last update can very easy with this command<br>
`uv sync`<br>

### 3. Environment Variables
Copy all environment Variables into `.env`. it'll use for saving and accessing our variable such as `OPENAI_API_KEY` etc.

## Run the program
### 1. Local
Since you still on the parent program, you can run this command<br>
`uvicorn main:app --host 127.0.0.1 --port 8080 --reload`

### 2. Docker
You can run it as container using Docker by run this command<br>
`docker compose up -d --build`<br>
Make sure that everything run well from installing the packages and run the program on your terminal or docker desktop terminal.

# API Documentation
When the application is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs

The API includes a health check endpoint at /health that verifies the application and (will be) database connection status.