@description('Name of the Azure Key Vault')
param keyVaultName string

@description('The Azure region for Key Vault')
param location string = 'westeurope' // Set to West Europe for GDPR compliance

// Provision Azure Key Vault
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
