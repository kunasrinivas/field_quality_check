@description('Name of the Cosmos DB account (globally unique)')
param cosmosAccountName string

@description('Azure region')
param location string = 'westeurope'

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosAccountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    capabilities: [
      {
        // Serverless — no capacity planning needed for dev; swap to provisioned for prod
        name: 'EnableServerless'
      }
    ]
    enableAutomaticFailover: false
    publicNetworkAccess: 'Enabled'
    minimalTlsVersion: 'Tls12'
    disableLocalAuth: false
  }
}

resource cosmosDatabase 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosAccount
  name: 'fqct-data'
  properties: {
    resource: {
      id: 'fqct-data'
    }
  }
}

// AI decisions, approval records, rework requests — queried per work order
resource auditTrailContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'audit-trail'
  properties: {
    resource: {
      id: 'audit-trail'
      partitionKey: {
        paths: ['/workOrderId']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
      }
    }
  }
}

// Full agent conversation turns — queried per session
resource agentConversationsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'agent-conversations'
  properties: {
    resource: {
      id: 'agent-conversations'
      partitionKey: {
        paths: ['/sessionId']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
      }
    }
  }
}

// Semi-structured work order metadata — queried per contractor
resource workOrdersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: cosmosDatabase
  name: 'work-orders'
  properties: {
    resource: {
      id: 'work-orders'
      partitionKey: {
        paths: ['/contractorId']
        kind: 'Hash'
        version: 2
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
      }
    }
  }
}

output cosmosAccountEndpoint string = cosmosAccount.properties.documentEndpoint
output cosmosDatabaseName string = cosmosDatabase.name
