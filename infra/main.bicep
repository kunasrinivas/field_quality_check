@description('Azure region for all resources')
param location string = 'westeurope'

@description('Azure region for SQL Server — westeurope has provisioning restrictions in some subscriptions')
param sqlLocation string = 'northeurope'

@description('Deterministic unique suffix derived from the resource group ID — reused across all globally-scoped resource names')
param resourceSuffix string = uniqueString(resourceGroup().id)

@description('Name of the Key Vault')
param keyVaultName string = 'fqct-kv-dev'

@description('SQL Server administrator login')
param sqlAdminLogin string = 'fqctadmin'

@secure()
@description('SQL Server administrator password — passed as a secret, never stored in parameters files')
param sqlAdminPassword string

@description('Publisher email for API Management notifications. Set to empty string to skip APIM deployment (free-tier subscriptions may lack quota).')
param apimPublisherEmail string = ''

// All globally-scoped names derived from the same suffix
var storageAccountName  = 'fqctstg${resourceSuffix}'
var sqlServerName        = 'fqct-sql-${take(resourceSuffix, 8)}'
var sqlDatabaseName      = 'fqct-db-dev'
var cosmosAccountName    = 'fqct-cosmos-${take(resourceSuffix, 8)}'
var functionAppName      = 'fqct-func-${take(resourceSuffix, 8)}'
var funcStorageName      = 'fqctfnstg${take(resourceSuffix, 8)}'
var planName             = 'fqct-plan-dev'
var apimName             = 'fqct-apim-${take(resourceSuffix, 8)}'
var deployApim           = !empty(apimPublisherEmail)

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
    location: sqlLocation
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

// Functions depends on storage (implicit via output ref), sql (implicit via output ref),
// and cosmos (explicit dependsOn — cosmosAccountName is a string so ARM can't infer it).
// Without dependsOn, ARM deploys Functions and Cosmos in parallel and listConnectionStrings()
// fails because Cosmos hasn't reached a running state yet.
module functions './modules/functions.bicep' = {
  name: 'FunctionsDeployment'
  dependsOn: [cosmos]
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

// APIM is skipped when apimPublisherEmail is empty (free-tier subscriptions).
// Set the APIM_PUBLISHER_EMAIL GitHub Secret to enable it.
module apim './modules/apim.bicep' = if (deployApim) {
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
#disable-next-line BCP318
output apimGatewayUrl       string = deployApim ? apim.outputs!.apimGatewayUrl : 'APIM not deployed — set APIM_PUBLISHER_EMAIL secret to enable'
