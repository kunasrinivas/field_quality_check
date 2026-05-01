module storage './modules/storage.bicep' = {
  name: 'StorageDeployment'
  params: {
    location: 'westeurope'
    storageAccountName: 'fqcstoragedev'
  }
}