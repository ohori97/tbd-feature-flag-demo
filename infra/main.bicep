param location string = resourceGroup().location
param acrName string = 'acrtbddemo${uniqueString(resourceGroup().id)}'
param appConfigName string = 'appconftbddemo${uniqueString(resourceGroup().id)}'
param aciName string = 'aci-tbd-demo'
param image string

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

resource appConfig 'Microsoft.AppConfiguration/configurationStores@2023-03-01' = {
  name: appConfigName
  location: location
  sku: {
    name: 'standard'
  }
}

var keyValues = [
  {
    name: '.appconfig.featureflag~2FGreetingFeature'
    value: '{"id": "GreetingFeature", "description": "Enable new greeting message", "enabled": false, "conditions": {"client_filters": []}}'
    contentType: 'application/vnd.microsoft.appconfig.ff+json;charset=utf-8'
  }
  {
    name: 'Sentinel'
    value: '1'
    contentType: 'text/plain'
  }
]

resource configKeys 'Microsoft.AppConfiguration/configurationStores/keyValues@2023-03-01' = [for kv in keyValues: {
  parent: appConfig
  name: kv.name
  properties: {
    value: kv.value
    contentType: kv.contentType
  }
}]

resource aci 'Microsoft.ContainerInstance/containerGroups@2023-05-01' = {
  name: aciName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    osType: 'Linux'
    containers: [
      {
        name: 'app'
        properties: {
          image: image
          resources: {
            requests: {
              cpu: 1
              memoryInGB: 1
            }
          }
          ports: [
            {
              port: 80
              protocol: 'TCP'
            }
          ]
          environmentVariables: [
            {
              name: 'APP_CONFIG_ENDPOINT'
              value: appConfig.properties.endpoint
            }
          ]
        }
      }
    ]
    ipAddress: {
      type: 'Public'
      ports: [
        {
          port: 80
          protocol: 'TCP'
        }
      ]
      dnsNameLabel: 'aci-tbd-demo-${uniqueString(resourceGroup().id)}'
    }
    imageRegistryCredentials: [
      {
        server: acr.properties.loginServer
        username: acr.name
        password: acr.listCredentials().passwords[0].value
      }
    ]
  }
}

// App Configuration Data Reader role definition ID
var appConfigDataReaderRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '516239f1-63e1-4d78-a4de-a74fb236a071')

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appConfig.id, aci.id, appConfigDataReaderRoleId)
  scope: appConfig
  properties: {
    roleDefinitionId: appConfigDataReaderRoleId
    principalId: aci.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output aciFqdn string = aci.properties.ipAddress.fqdn
output acrLoginServer string = acr.properties.loginServer
