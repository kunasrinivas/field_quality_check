@description('The location where the resources will be created')
param location string

@description('Name of the storage account')
param storageAccountName string = 'fqcstoragedev'

resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS' // Locally redundant storage
    tier: 'Standard'
  }
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    supportsHttpsTrafficOnly: true
  }
}

resource rawEvidenceContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = {
  name: '${storageAccount.name}/default/raw-evidence'
  dependsOn: [
    storageAccount
  ]
  properties: {
    publicAccess: 'None'
  }
}

resource processedEvidenceContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = {
  name: '${storageAccount.name}/default/processed-evidence'
  dependsOn: [
    storageAccount
  ]
  properties: {
    publicAccess: 'None'
  }
}

output storageAccountName string = storageAccount.name