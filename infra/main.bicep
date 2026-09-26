targetScope = 'resourceGroup'

@description('Azure region for resources.')
param location string = resourceGroup().location

@description('Deployment Environment, dev/prod.')
param environment string

var suffix = uniqueString(subscription().id, resourceGroup().id)
var commonTags = {
  project: 'dataops-copilot'
  environment: environment
  managedBy: 'bicep'
}

var containerRegistryName = 'acrdataops${suffix}'
var logAnalyticsName = 'log-dataops-${environment}'
var containerEnviornmentName = 'cae-dataops${suffix}'
var keyVaultName = 'kvdataops${suffix}'

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2026-03-01' = {
  location:location
  name: logAnalyticsName
  tags: commonTags
  properties:{sku:{
    name: 'PerGB2018'
  }
  retentionInDays: 30
  features:{
    enableLogAccessUsingOnlyResourcePermissions: true
  }
}
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2025-11-01' = {
  name: containerRegistryName
  location: location
  tags: commonTags
  sku: {name: 'Basic'}
  properties:{
    adminUserEnabled:false
    publicNetworkAccess: 'Enabled'
   }
}

resource containerEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerEnviornmentName
  location: location
  tags: commonTags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2025-05-01' = {
  name: keyVaultName
  location: location
  tags: commonTags
  properties: {
    tenantId: tenant().tenantId
    sku: {
      family: 'A'
      name: 'standard'
    }
    enableRbacAuthorization: true
    publicNetworkAccess: 'Enabled'
  }
}


output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerEnvironmentId string = containerEnvironment.id
output keyVaultUri string = keyVault.properties.vaultUri
