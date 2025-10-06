@description('AKS Cluster Name')
param aksName string

@description('Environment name (qa, prod)')
param environment string

@description('Location for deployment')
param location string

@description('Subnet Resource ID')
param subnetId string

@description('Minimum node count')
param nodeMinCount int

@description('Maximum node count')
param nodeMaxCount int

@description('VM size for nodes')
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
    }
    nodeResourceGroup: 'MC_azne-rg-roanon-t-aahelp_${aksName}_${location}'
    enableRBAC: true
    storageProfile: {
      diskCSIDriver: { enabled: true }
      fileCSIDriver: { enabled: true }
      snapshotController: { enabled: true }
    }
    oidcIssuerProfile: {
      enabled: true
    }
  }
}
