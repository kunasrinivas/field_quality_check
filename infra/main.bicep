@description('Azure region for all resources')
param location string = 'westeurope'

@description('Deterministic unique suffix derived from the resource group ID — reused across all globally-scoped resource names')
param resourceSuffix string = uniqueString(resourceGroup().id)

@description('Name of the Key Vault')
param keyVaultName string = 'fqct-kv-dev'

@description('SQL Server administrator login')
param sqlAdminLogin string = 'fqctadmin'

@secure()
@description('SQL Server administrator password — passed as a secret, never stored in parameters files')
param sqlAdminPassword string

@description('Publisher email for API Management notifications')
param apimPublisherEmail string

// All globally-scoped names derived from the same suffix
var storageAccountName  = 'fqctstg${resourceSuffix}'
var sqlServerName        = 'fqct-sql-${take(resourceSuffix, 8)}'
var sqlDatabaseName      = 'fqct-db-dev'
var cosmosAccountName    = 'fqct-cosmos-${take(resourceSuffix, 8)}'
var functionAppName      = 'fqct-func-${take(resourceSuffix, 8)}'
var funcStorageName      = 'fqctfnstg${take(resourceSuffix, 8)}'
var planName             = 'fqct-plan-dev'
var apimName             = 'fqct-apim-${take(resourceSuffix, 8)}'

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

module sql './modules/sql.bicep' = {
  name: 'SqlDeployment'
  params: {
    location: location
    sqlServerName: sqlServerName
    sqlDatabaseName: sqlDatabaseName
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
  }
}

module cosmos './modules/cosmosdb.bicep' = {
  name: 'CosmosDeployment'
  params: {
    location: location
    cosmosAccountName: cosmosAccountName
  }
}

// Functions depends on storage, sql, and cosmos — implicit via param references
module functions './modules/functions.bicep' = {
  name: 'FunctionsDeployment'
  params: {
    location: location
    functionAppName: functionAppName
    funcStorageName: funcStorageName
    planName: planName
    evidenceStorageAccountName: storage.outputs.storageAccountName
    cosmosAccountName: cosmosAccountName
    sqlServerFqdn: sql.outputs.sqlServerFqdn
    sqlDatabaseName: sql.outputs.sqlDatabaseName
    sqlAdminLogin: sqlAdminLogin
    sqlAdminPassword: sqlAdminPassword
  }
}

// APIM depends on functions hostname — implicit via param reference
module apim './modules/apim.bicep' = {
  name: 'ApimDeployment'
  params: {
    location: location
    apimName: apimName
    publisherEmail: apimPublisherEmail
    functionAppHostname: functions.outputs.functionAppHostname
  }
}

output storageAccountName  string = storageAccountName
output sqlServerFqdn        string = sql.outputs.sqlServerFqdn
output cosmosAccountName    string = cosmosAccountName
output functionAppName      string = functions.outputs.functionAppName
output functionAppHostname  string = functions.outputs.functionAppHostname
output apimGatewayUrl       string = apim.outputs.apimGatewayUrl
