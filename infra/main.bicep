@description('Azure region for all resources')
param location string = 'westeurope'

@description('Name of the storage account')
param storageAccountName string = 'fqcstoragedev'

@description('Name of the Key Vault')
param keyVaultName string = 'fqct-kv-main'

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
