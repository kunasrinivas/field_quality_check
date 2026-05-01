@description('Name of the Azure Key Vault')
param keyVaultName string

@description('The Azure region for Key Vault (GDPR-compliant default)')
param location string = 'westeurope'

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
  }
}
