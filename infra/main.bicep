targetScope = 'resourceGroup'

@description('Azure region for resources.')
param location string = resourceGroup().location

@description('Deployment Environment, dev/prod.')
param environment string

@description('Immutable ACR image URI')
param containerImage string

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
var containerAppName = 'ca-dataops-${environment}'
var containerIdName = 'id-dataops-${environment}'

var acrPullRoleDefinitionId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

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

resource containerAppIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: containerIdName
  location: location
  tags: commonTags
}

resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: containerRegistry
  name: guid(
    containerRegistry.id,
    containerAppIdentity.name,
    acrPullRoleDefinitionId
  )
    properties: {
    principalId: containerAppIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      acrPullRoleDefinitionId
    )
  }
}

resource containerApp 'Microsoft.App/containerApps@2026-01-01' = {
  name: containerAppName
  location: location
  tags: commonTags
  dependsOn: [acrPullRoleAssignment]
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${containerAppIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: containerAppIdentity.id
        }
      ]
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'dataops-copilot'
          image: containerImage
          resources: {
            cpu: any('0.25')
            memory: '0.5Gi'
          }
          probes: [
            {
              type: 'Startup'
              httpGet: {
                path: '/healthz'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 3
              periodSeconds: 10
              timeoutSeconds: 3
              failureThreshold: 10
            }
            {
              type: 'Readiness'
              httpGet: {
                path: '/healthz'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 5
              periodSeconds: 10
              timeoutSeconds: 3
              failureThreshold: 3
            }
            {
              type: 'Liveness'
              httpGet: {
                path: '/healthz'
                port: 8000
                scheme: 'HTTP'
              }
              initialDelaySeconds: 10
              periodSeconds: 30
              timeoutSeconds: 3
              failureThreshold: 3
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 2
      }
    }
  }
}



output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerEnvironmentId string = containerEnvironment.id
output keyVaultUri string = keyVault.properties.vaultUri
output containerAppName string = containerApp.name
output containerAppUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
