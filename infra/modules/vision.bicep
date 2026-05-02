@description('Name of the Azure AI Vision resource (globally unique)')
param visionName string

@description('Azure region — Computer Vision is available in northeurope and westeurope')
param location string = 'northeurope'

@description('SKU: F0 = free tier (5 000 calls/month, 20/min), S1 = standard pay-per-call')
param sku string = 'S1'

resource visionAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: visionName
  location: location
  kind: 'ComputerVision'
  sku: {
    name: sku
  }
  properties: {
    publicNetworkAccess: 'Enabled'
  }
}

output visionEndpoint string = visionAccount.properties.endpoint
output visionAccountName string = visionAccount.name
