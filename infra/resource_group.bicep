@description('The name of the resource group to create')
param resourceGroupName string

@description('The Azure region for the resource group')
param location string = 'westeurope' // GDPR priority for Western Europe

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
}