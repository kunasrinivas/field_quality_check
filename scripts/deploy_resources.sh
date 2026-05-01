#!/bin/bash

set -e

# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------
RESOURCE_GROUP="FQCT-ResourceGroup"
LOCATION="westeurope"
KEYVAULT_NAME="fqct-kv-$(openssl rand -hex 3)"   # globally unique
SERVICE_PRINCIPAL_NAME="KeyVaultSP"

echo "Using Key Vault name: $KEYVAULT_NAME"


# ---------------------------------------------------------
# Ensure Resource Group exists
# ---------------------------------------------------------
echo "Checking Resource Group..."
RG_LOCATION=$(az group show --name $RESOURCE_GROUP --query location -o tsv || true)

if [ -z "$RG_LOCATION" ]; then
  echo "Creating Resource Group: $RESOURCE_GROUP in $LOCATION"
  az group create --name $RESOURCE_GROUP --location $LOCATION
else
  echo "Resource Group already exists in: $RG_LOCATION"
  LOCATION=$RG_LOCATION
fi


# ---------------------------------------------------------
# Retrieve or create Service Principal
# ---------------------------------------------------------
echo "Checking for service principal: $SERVICE_PRINCIPAL_NAME..."
SP_APPID=$(az ad sp list --display-name $SERVICE_PRINCIPAL_NAME --query "[0].appId" -o tsv || true)

if [ -z "$SP_APPID" ]; then
  echo "Service principal not found. Creating..."
  SP_OUTPUT=$(az ad sp create-for-rbac \
    --name $SERVICE_PRINCIPAL_NAME \
    --role contributor \
    --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP)

  SP_APPID=$(echo "$SP_OUTPUT" | jq -r '.appId')
fi

SERVICE_PRINCIPAL_OBJECT_ID=$(az ad sp show --id $SP_APPID --query id -o tsv)

if [ -z "$SERVICE_PRINCIPAL_OBJECT_ID" ]; then
  echo "ERROR: Could not resolve service principal object ID."
  exit 1
fi

echo "Using SP Object ID: $SERVICE_PRINCIPAL_OBJECT_ID"


# ---------------------------------------------------------
# Handle soft-deleted Key Vaults
# ---------------------------------------------------------
echo "Checking for soft-deleted Key Vaults..."
RECOVERABLE=$(az keyvault list-deleted --query "[?name=='$KEYVAULT_NAME']" -o tsv || true)

if [ ! -z "$RECOVERABLE" ]; then
  echo "Purging soft-deleted Key Vault..."
  az keyvault purge --name $KEYVAULT_NAME --location $LOCATION
  sleep 10
fi


# ---------------------------------------------------------
# Create Key Vault (RBAC mode)
# ---------------------------------------------------------
echo "Creating Key Vault: $KEYVAULT_NAME..."
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --enable-rbac-authorization true


# ---------------------------------------------------------
# Assign RBAC roles to the Service Principal
# ---------------------------------------------------------
VAULT_ID=$(az keyvault show --name $KEYVAULT_NAME --query id -o tsv)

echo "Assigning RBAC roles..."

# Secrets
az role assignment create \
  --role "Key Vault Secrets Officer" \
  --assignee-object-id $SERVICE_PRINCIPAL_OBJECT_ID \
  --scope $VAULT_ID

# Keys
az role assignment create \
  --role "Key Vault Crypto Officer" \
  --assignee-object-id $SERVICE_PRINCIPAL_OBJECT_ID \
  --scope $VAULT_ID

# Certificates
az role assignment create \
  --role "Key Vault Certificates Officer" \
  --assignee-object-id $SERVICE_PRINCIPAL_OBJECT_ID \
  --scope $VAULT_ID

echo "---------------------------------------------------------"
echo "Key Vault + RBAC setup completed successfully."
echo "Key Vault Name: $KEYVAULT_NAME"
echo "Service Principal: $SERVICE_PRINCIPAL_NAME"
echo "---------------------------------------------------------"
