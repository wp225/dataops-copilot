targetScope = 'subscription'

@description('Azure location for this environment.')
param location string = 'westus2'

@description('Resource group name.')
param resourcegroupName string

@description('Environment name, dev/prod')
param environment string

resource projectResourceGroup 'Microsoft.Resources/resourceGroups@2025-04-01' = {
  name:resourcegroupName
  location:location
  tags:{
    project: 'dataops-copilot'
    environment: environment
    managedBy: 'bicep'
  }
}
