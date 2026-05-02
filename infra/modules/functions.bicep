@description('Name of the Function App (globally unique)')
param functionAppName string

@description('Name of the App Service Plan')
param planName string

@description('Name of the Functions runtime storage account (separate from evidence storage)')
param funcStorageName string

@description('Azure region')
param location string = 'westeurope'

@description('Name of the evidence storage account — used for the raw-evidence blob trigger')
param evidenceStorageAccountName string

@description('Name of the Cosmos DB account')
param cosmosAccountName string

@description('Fully qualified domain name of the SQL Server')
param sqlServerFqdn string

@description('Name of the SQL Database')
param sqlDatabaseName string

@description('SQL Server admin login')
param sqlAdminLogin string

@secure()
@description('SQL Server admin password')
param sqlAdminPassword string

// Dedicated storage account for Functions runtime state (separate from application data)
resource funcStorage 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: funcStorageName
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

// Compute connection strings at deploy time — never stored in files
var funcStorageConnection = 'DefaultEndpointsProtocol=https;AccountName=${funcStorage.name};AccountKey=${funcStorage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'

var evidenceStorageKey = listKeys(resourceId('Microsoft.Storage/storageAccounts', evidenceStorageAccountName), '2022-09-01').keys[0].value
var evidenceStorageConnection = 'DefaultEndpointsProtocol=https;AccountName=${evidenceStorageAccountName};AccountKey=${evidenceStorageKey};EndpointSuffix=${environment().suffixes.storage}'

var cosmosConnection = listConnectionStrings(resourceId('Microsoft.DocumentDB/databaseAccounts', cosmosAccountName), '2023-04-15').connectionStrings[0].connectionString

// Driver prefix required by pyodbc on Linux — ODBC Driver 18 ships on the Functions runtime image
var sqlConnection = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:${sqlServerFqdn},1433;Initial Catalog=${sqlDatabaseName};UID=${sqlAdminLogin};PWD=${sqlAdminPassword};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

// Linux Consumption plan — required for Python Functions
resource appServicePlan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: planName
  location: location
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource functionApp 'Microsoft.Web/sites@2022-09-01' = {
  name: functionAppName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      appSettings: [
        { name: 'AzureWebJobsStorage',        value: funcStorageConnection }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME',    value: 'python' }
        { name: 'EVIDENCE_STORAGE_CONNECTION', value: evidenceStorageConnection }
        { name: 'COSMOS_CONNECTION',           value: cosmosConnection }
        { name: 'SQL_CONNECTION',              value: sqlConnection }
        { name: 'EVIDENCE_CONTAINER',          value: 'raw-evidence' }
        { name: 'COSMOS_DB_NAME',              value: 'fqct-data' }
      ]
    }
  }
}

output functionAppName string = functionApp.name
output functionAppHostname string = functionApp.properties.defaultHostName
output functionAppPrincipalId string = functionApp.identity.principalId
