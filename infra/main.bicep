@description('Azure region for all resources')
param location string = 'westeurope'

@description('Azure region for SQL Server — westeurope has provisioning restrictions in some subscriptions')
param sqlLocation string = 'northeurope'

@description('Azure region for Cosmos DB — westeurope has capacity constraints for zonal redundant accounts')
param cosmosLocation string = 'northeurope'

@description('Azure region for Azure AI Vision — northeurope and westeurope both supported')
param visionLocation string = 'northeurope'

@description('Deterministic unique suffix derived from the resource group ID — reused across all globally-scoped resource names')
param resourceSuffix string = uniqueString(resourceGroup().id)

@description('SQL Server administrator login')
param sqlAdminLogin string = 'fqctadmin'

@secure()
@description('SQL Server administrator password — passed as a secret, never stored in parameters files')
param sqlAdminPassword string

@description('Publisher email for API Management notifications. Leave empty to skip APIM deployment (free-tier subscriptions may lack quota).')
param apimPublisherEmail string = ''

// All globally-scoped names derived from the same suffix — never hard-coded to avoid
// soft-delete conflicts on Key Vault and global-uniqueness collisions on storage/cosmos.
var storageAccountName  = 'fqctstg${resourceSuffix}'
var keyVaultName         = 'fqct-kv-${take(resourceSuffix, 8)}'
var sqlServerName        = 'fqct-sql-${take(resourceSuffix, 8)}'
var sqlDatabaseName      = 'fqct-db-dev'
var cosmosAccountName    = 'fqct-cosmos-${take(resourceSuffix, 8)}'
var visionName           = 'fqct-vision-${take(resourceSuffix, 8)}'
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
    location: cosmosLocation
    cosmosAccountName: cosmosAccountName
  }
}

module vision './modules/vision.bicep' = {
  name: 'VisionDeployment'
  params: {
    location: visionLocation
    visionName: visionName
  }
}

// Functions depends on storage (implicit via output ref), sql (implicit via output ref),
// cosmos (explicit dependsOn — cosmosAccountName is a string so ARM can't infer it),
// and vision (implicit via visionEndpoint output ref).
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
    visionEndpoint: vision.outputs.visionEndpoint
    visionAccountName: vision.outputs.visionAccountName
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
output keyVaultName         string = keyVault.outputs.keyVaultName
output sqlServerFqdn        string = sql.outputs.sqlServerFqdn
output cosmosAccountName    string = cosmosAccountName
output visionEndpoint       string = vision.outputs.visionEndpoint
output functionAppName      string = functions.outputs.functionAppName
output functionAppHostname  string = functions.outputs.functionAppHostname
// apimGatewayUrl omitted when APIM is conditional — ARM cannot safely evaluate
// a conditional module output as a typed string when the module may not have run.
