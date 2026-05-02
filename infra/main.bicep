@description('Azure region for all resources')
param location string = 'westeurope'

@description('Unique suffix derived from the resource group — keeps the storage account name globally unique and repeatable')
param storageUniqueSuffix string = uniqueString(resourceGroup().id)

@description('Name of the Key Vault')
param keyVaultName string = 'fqct-kv-dev'

var storageAccountName = 'fqctstg${storageUniqueSuffix}'

module storage './modules/storage.bicep' = {
  name: 'StorageDeployment'
  params: {
    location: location
    storageAccountName: storageAccountName
  }
}

module keyVault './modules/keyvault.bicep' = {
  name: 'KeyVaultDeployment'
  params: {
    location: location
    keyVaultName: keyVaultName
  }
}

output storageAccountName string = storageAccountName
