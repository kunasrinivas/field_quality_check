@description('Name of the Azure Key Vault')
param keyVaultName string

@description('The name of the resource group where Key Vault will be deployed')
param resourceGroupName string

@description('The Azure region for Key Vault')
param location string = 'westeurope' // Compliance with GDPR

resource keyVault 'Microsoft.KeyVault/vaults@2021-11-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    softDeleteRetentionInDays: 90
    enableSoftDelete: true
  }
}