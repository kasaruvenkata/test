@description('AKS Cluster Name')
param aksName string

@description('Environment name (qa, prod)')
param environment string

@description('Deployment location')
param location string

@description('Subnet Resource ID for node pool')
param subnetId string

@description('Log Analytics workspace resource ID')
param logWorkspaceId string

@description('Node count minimum')
param nodeMinCount int

@description('Node count maximum')
param nodeMaxCount int

@description('Node VM size')
param nodeVmSize string

@description('Kubernetes version')
param kubernetesVersion string

resource aksCluster 'Microsoft.ContainerService/managedClusters@2025-05-01' = {
  name: aksName
  location: location
  tags: {
    Application_Name: 'AAHELP'
    Environment: environment
    Project: 'ROOTF'
    Region: location
  }
  sku: {
    name: 'Base'
    tier: 'Free'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: kubernetesVersion
    dnsPrefix: '${aksName}-dns'
    agentPoolProfiles: [
      {
        name: 'agentpool'
        count: nodeMinCount
        vmSize: nodeVmSize
        osDiskSizeGB: 150
        osDiskType: 'Ephemeral'
        vnetSubnetID: subnetId
        type: 'VirtualMachineScaleSets'
        enableAutoScaling: true
        minCount: nodeMinCount
        maxCount: nodeMaxCount
        mode: 'System'
        osType: 'Linux'
        osSKU: 'Ubuntu'
      }
    ]
    networkProfile: {
      networkPlugin: 'azure'
      networkPolicy: 'azure'
      loadBalancerSku: 'Standard'
      serviceCidr: '172.16.50.0/24'
      dnsServiceIP: '172.16.50.10'
      outboundType: 'loadBalancer'
    }
    addonProfiles: {
      azurepolicy: {
        enabled: true
      }
      azureKeyvaultSecretsProvider: {
        enabled: true
        config: {
          enableSecretRotation: 'true'
        }
      }
    }
    nodeResourceGroup: 'MC_azne-rg-roanon-t-aahelp_${aksName}_${location}'
    enableRBAC: true
    securityProfile: {
      defender: {
        logAnalyticsWorkspaceResourceId: logWorkspaceId
        securityMonitoring: {
          enabled: true
        }
      }
      imageCleaner: {
        enabled: true
        intervalHours: 168
      }
      workloadIdentity: {
        enabled: true
      }
    }
    storageProfile: {
      diskCSIDriver: { enabled: true }
      fileCSIDriver: { enabled: true }
      snapshotController: { enabled: true }
    }
    oidcIssuerProfile: { enabled: true }
  }
}
