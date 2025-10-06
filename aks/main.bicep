@description('Environment name (e.g. qa, prod)')
param environment string = 'qa'

@description('Location of deployment')
param location string = 'northeurope'

@description('AKS cluster name')
param aksName string

@description('Virtual Network name')
param vnetName string

@description('Subnet name for AKS agent pool')
param subnetName string

@description('Resource group of the existing VNet')
param vnetResourceGroup string

@description('Subscription ID')
param subscriptionId string

@description('Log Analytics workspace resource ID')
param logWorkspaceId string

@description('Node count minimum')
param nodeMinCount int = 2

@description('Node count maximum')
param nodeMaxCount int = 5

@description('Node VM size')
param nodeVmSize string = 'Standard_D4ds_v5'

@description('AKS Kubernetes version')
param kubernetesVersion string = '1.32.7'


// build vnet and subnet id dynamically
var vnetId = '/subscriptions/${subscriptionId}/resourceGroups/${vnetResourceGroup}/providers/Microsoft.Network/virtualNetworks/${vnetName}'
var subnetId = '${vnetId}/subnets/${subnetName}'

module aks 'modules/aks.bicep' = {
  name: '${aksName}-deployment'
  params: {
    aksName: aksName
    environment: environment
    location: location
    subnetId: subnetId
    logWorkspaceId: logWorkspaceId
    nodeMinCount: nodeMinCount
    nodeMaxCount: nodeMaxCount
    nodeVmSize: nodeVmSize
    kubernetesVersion: kubernetesVersion
  }
}
