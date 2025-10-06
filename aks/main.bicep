@description('Environment name (qa, prod)')
param environment string = 'qa'

@description('Deployment location')
param location string = 'northeurope'

@description('AKS cluster name')
param aksName string

@description('Virtual network name')
param vnetName string

@description('Subnet name for AKS agent pool')
param subnetName string

@description('Resource group containing the VNet')
param vnetResourceGroup string

@description('Azure subscription ID')
param subscriptionId string

@description('Minimum node count')
param nodeMinCount int = 2

@description('Maximum node count')
param nodeMaxCount int = 5

@description('VM size for agent nodes')
param nodeVmSize string = 'Standard_D4ds_v5'

@description('Kubernetes version')
param kubernetesVersion string = '1.32.7'

// Build full VNet and Subnet IDs
var vnetId = '/subscriptions/${subscriptionId}/resourceGroups/${vnetResourceGroup}/providers/Microsoft.Network/virtualNetworks/${vnetName}'
var subnetId = '${vnetId}/subnets/${subnetName}'

// Include AKS module
module aks 'modules/aks.bicep' = {
  name: '${aksName}-deployment'
  params: {
    aksName: aksName
    environment: environment
    location: location
    subnetId: subnetId
    nodeMinCount: nodeMinCount
    nodeMaxCount: nodeMaxCount
    nodeVmSize: nodeVmSize
    kubernetesVersion: kubernetesVersion
  }
}
