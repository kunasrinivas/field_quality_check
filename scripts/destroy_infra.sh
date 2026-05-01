#!/bin/bash

# Configuration
RESOURCE_GROUP="FQCT-ResourceGroup"
KEYVAULT_NAME="FQCT-KeyVault"

# Delete Key Vault (Optional)
echo "Attempting to delete Key Vault: $KEYVAULT_NAME..."
az keyvault delete --name $KEYVAULT_NAME || echo "Key Vault $KEYVAULT_NAME not found or already deleted."

# Delete Resource Group
echo "Deleting Resource Group: $RESOURCE_GROUP..."
az group delete --name $RESOURCE_GROUP --yes --no-wait || echo "Resource Group $RESOURCE_GROUP not found or already deleted."

echo "Cleanup completed successfully."
