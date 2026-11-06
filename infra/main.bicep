targetScope = 'resourceGroup'

@description('Azure region for resources.')
param location string = resourceGroup().location

@description('Deployment Environment, dev/prod.')
param environment string

@description('Deploy the Container App. Leave false until Key Vault secrets and the image exist.')
param deployApp bool = false

@description('Container image to run, e.g. <acr>.azurecr.io/dataops-copilot:<tag>.')
param containerImage string = ''

@description('Claude model used by the investigation agent.')
param anthropicModel string = 'claude-opus-5-5'

@description('Send LangSmith traces. Requires a langsmith-api-key secret in Key Vault.')
param enableLangSmith bool = false

@description('LangSmith project name for traces.')
param langSmithProject string = 'dataops-copilot'

@description('Object ID of the deploying user; granted secret and blob write access. Empty to skip.')
param deployerPrincipalId string = ''

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
var storageAccountName = 'stdataops${suffix}'
var identityName = 'id-dataops-${environment}'
var containerAppName = 'ca-dataops-${environment}'
var reportsContainerName = 'dataops'
var rawContainerName = 'raw'

// Built-in role definition IDs.
var roles = {
  acrPull: '7f951dda-4ed3-4680-a7ca-43fe172d538d'
  storageBlobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  keyVaultSecretsUser: '4633458b-17de-408a-b874-0445c86b69e6'
  keyVaultSecretsOfficer: 'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'
}

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

// --- Data lake: ADLS Gen2 for raw batches and RCA report history ---

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: commonTags
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    isHnsEnabled: true
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storageAccount
  name: 'default'
}

resource reportsContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: reportsContainerName
}

resource rawContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: rawContainerName
}

// --- Identity and least-privilege access for the app ---

resource appIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: commonTags
}

resource appAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, appIdentity.id, roles.acrPull)
  scope: containerRegistry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.acrPull)
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource appBlobAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, appIdentity.id, roles.storageBlobDataContributor)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.storageBlobDataContributor)
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource appSecretsAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, appIdentity.id, roles.keyVaultSecretsUser)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.keyVaultSecretsUser)
    principalId: appIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource deployerSecretsAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(keyVault.id, deployerPrincipalId, roles.keyVaultSecretsOfficer)
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.keyVaultSecretsOfficer)
    principalId: deployerPrincipalId
    principalType: 'User'
  }
}

resource deployerBlobAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(storageAccount.id, deployerPrincipalId, roles.storageBlobDataContributor)
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.storageBlobDataContributor)
    principalId: deployerPrincipalId
    principalType: 'User'
  }
}

// --- The API container app ---

var baseSecrets = [
  {
    name: 'anthropic-api-key'
    keyVaultUrl: '${keyVault.properties.vaultUri}secrets/anthropic-api-key'
    identity: appIdentity.id
  }
]
var langSmithSecrets = enableLangSmith
  ? [
      {
        name: 'langsmith-api-key'
        keyVaultUrl: '${keyVault.properties.vaultUri}secrets/langsmith-api-key'
        identity: appIdentity.id
      }
    ]
  : []

var baseEnv = [
  { name: 'ANTHROPIC_API_KEY', secretRef: 'anthropic-api-key' }
  { name: 'AZURE_CLIENT_ID', value: appIdentity.properties.clientId }
  { name: 'DATAOPS_ANTHROPIC_MODEL', value: anthropicModel }
  { name: 'DATAOPS_REPORT_STORE', value: 'adls' }
  { name: 'DATAOPS_ADLS_ACCOUNT_URL', value: storageAccount.properties.primaryEndpoints.blob }
  { name: 'DATAOPS_ADLS_CONTAINER', value: reportsContainerName }
]
var langSmithEnv = enableLangSmith
  ? [
      { name: 'LANGSMITH_TRACING', value: 'true' }
      { name: 'LANGSMITH_PROJECT', value: langSmithProject }
      { name: 'LANGSMITH_API_KEY', secretRef: 'langsmith-api-key' }
    ]
  : []

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = if (deployApp) {
  name: containerAppName
  location: location
  tags: commonTags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${appIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          identity: appIdentity.id
        }
      ]
      secrets: concat(baseSecrets, langSmithSecrets)
    }
    template: {
      containers: [
        {
          name: 'api'
          image: containerImage
          resources: {
            cpu: json('2.0')
            memory: '4Gi'
          }
          env: concat(baseEnv, langSmithEnv)
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/healthz', port: 8000 }
              initialDelaySeconds: 10
              periodSeconds: 30
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
  dependsOn: [
    appAcrPull
    appBlobAccess
    appSecretsAccess
  ]
}

output containerRegistryName string = containerRegistry.name
output storageAccountName string = storageAccount.name
output keyVaultName string = keyVault.name
output containerAppUrl string = deployApp ? 'https://${containerApp!.properties.configuration.ingress.fqdn}' : ''
output containerRegistryLoginServer string = containerRegistry.properties.loginServer
output containerEnvironmentId string = containerEnvironment.id
output keyVaultUri string = keyVault.properties.vaultUri
