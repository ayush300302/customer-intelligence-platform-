# deploy_azure.ps1
# PowerShell Deployment Script for deploying Customer Intelligence Platform to Azure Container Apps.

$resourceGroup = "rg-customer-intel"
$location = "eastus"
$acrName = "acrcustomerintel" + (Get-Random -Minimum 1000 -Maximum 9999)
$containerAppName = "ca-customer-intel"
$containerAppEnvName = "env-customer-intel"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Customer Intelligence Platform - Azure Deployment Script" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Azure CLI installation
Write-Host "`n[Step 1/6] Checking Azure CLI installation..." -ForegroundColor Yellow
if (-not (Get-Command "az" -ErrorAction SilentlyContinue)) {
    Write-Host "Azure CLI ('az') is not installed on this system." -ForegroundColor Red
    Write-Host "Please download and install it from: https://aka.ms/installazurecliwindows" -ForegroundColor Cyan
    Write-Host "After installation, restart your shell and re-run this script." -ForegroundColor Cyan
    Exit 1
} else {
    Write-Host "Azure CLI is installed." -ForegroundColor Green
}

# 2. Login to Azure
Write-Host "`n[Step 2/6] Logging in to Azure..." -ForegroundColor Yellow
Write-Host "A browser window will open. Please authenticate with your Azure account." -ForegroundColor Cyan
az login

# 3. Create Resource Group
Write-Host "`n[Step 3/6] Creating Resource Group: $resourceGroup in $location..." -ForegroundColor Yellow
az group create --name $resourceGroup --location $location

# 4. Create Azure Container Registry (ACR)
Write-Host "`n[Step 4/6] Creating Azure Container Registry: $acrName..." -ForegroundColor Yellow
az acr create --resource-group $resourceGroup --name $acrName --sku Basic --admin-enabled true

# Log in to ACR
Write-Host "Logging in to Azure Container Registry..." -ForegroundColor Yellow
az acr login --name $acrName

# 5. Build and Push Docker Image
$loginServer = (az acr show --name $acrName --query "loginServer" --output tsv)
$imageTag = "$loginServer/customer-intel:latest"

Write-Host "`n[Step 5/6] Building and pushing Docker image to ACR..." -ForegroundColor Yellow
Write-Host "Docker Target: $imageTag" -ForegroundColor Cyan

# Check if Docker Desktop/daemon is running
if (-not (Get-Service "docker" -ErrorAction SilentlyContinue) -and -not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker daemon is not running or Docker CLI is missing." -ForegroundColor Red
    Write-Host "Bypassing local docker build, using ACR task for remote building..." -ForegroundColor Yellow
    # Trigger remote build inside ACR (doesn't require local Docker!)
    az acr build --registry $acrName --image customer-intel:latest .
} else {
    Write-Host "Building image locally..." -ForegroundColor Cyan
    docker build -t customer-intel:latest .
    Write-Host "Tagging and pushing..." -ForegroundColor Cyan
    docker tag customer-intel:latest $imageTag
    docker push $imageTag
}

# 6. Deploy to Azure Container Apps
Write-Host "`n[Step 6/6] Registering Container Apps extension and deploying..." -ForegroundColor Yellow

# Ensure containerapp extension is installed
az extension add --name containerapp --upgrade

# Create Container App environment
Write-Host "Creating Container App Environment..." -ForegroundColor Yellow
az containerapp env create --name $containerAppEnvName --resource-group $resourceGroup --location $location

# Get ACR credentials
$registryUsername = (az acr credential show --name $acrName --query "username" --output tsv)
$registryPassword = (az acr credential show --name $acrName --query "passwords[0].value" --output tsv)

# Create Container App
Write-Host "Deploying Container App..." -ForegroundColor Yellow
az containerapp create `
  --name $containerAppName `
  --resource-group $resourceGroup `
  --environment $containerAppEnvName `
  --image $imageTag `
  --target-port 8000 `
  --ingress external `
  --registry-server $loginServer `
  --registry-username $registryUsername `
  --registry-password $registryPassword `
  --env-vars "GEMINI_API_KEY=your_gemini_api_key_here"

# Get URL
$fqdn = (az containerapp show --name $containerAppName --resource-group $resourceGroup --query "properties.configuration.ingress.fqdn" --output tsv)

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   Deployment Successful!" -ForegroundColor Green
Write-Host "   FastAPI Cloud Endpoint: http://$fqdn" -ForegroundColor Green
Write-Host "   Health Check: http://$fqdn/health" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
