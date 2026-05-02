@description('The location where the resources will be created')
param location string

@description('Name of the storage account')
param storageAccountName string = 'fqcstoragedev'

resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
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
  properties: {
    publicAccess: 'None'
  }
}

resource processedEvidenceContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2022-09-01' = {
  name: '${storageAccount.name}/default/processed-evidence'
  properties: {
    publicAccess: 'None'
  }
}

output storageAccountName string = storageAccount.name