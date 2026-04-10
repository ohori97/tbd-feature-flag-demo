#!/bin/bash
set -e

# Change directory to the script's location
cd "$(dirname "$0")"

RG_NAME="rg-tbd-demo"
LOCATION="japaneast"

echo "1. Creating Resource Group ($RG_NAME)..."
az group create --name $RG_NAME --location $LOCATION -o none

# Generate a unique suffix for ACR
SUB_ID=$(az account show --query id -o tsv)
UNIQUE_STR=$(echo -n "${SUB_ID}${RG_NAME}" | sha256sum | head -c 8 | tr '[:upper:]' '[:lower:]')
ACR_NAME="acrtbddemo${UNIQUE_STR}"

echo "2. Creating Azure Container Registry ($ACR_NAME)..."
az acr create --resource-group $RG_NAME --name $ACR_NAME --sku Basic --admin-enabled true -o none

IMAGE_NAME="${ACR_NAME}.azurecr.io/tbd-app:latest"

echo "3. Building Docker image using ACR Build..."
az acr build --registry $ACR_NAME --image tbd-app:latest ../src

echo "4. Deploying Bicep Template..."
az deployment group create \
  --resource-group $RG_NAME \
  --template-file ../infra/main.bicep \
  --parameters acrName=$ACR_NAME image=$IMAGE_NAME

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "Please wait a minute or two for ACI to pull the image and start."
echo "Use the FQDN to access the application:"
echo "========================================="
az deployment group show --resource-group $RG_NAME --name main --query properties.outputs.aciFqdn.value -o tsv
