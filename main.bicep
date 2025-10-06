param managedClusters_azne_aks_dev_t_aahelp_1_name string = 'azne-aks-dev-t-aahelp-1'
param virtualNetworks_azne_vnet_roanon_t_1_externalid string = '/subscriptions/d4655204-e89c-45ee-bd64-2705675e8513/resourceGroups/azne-rg-roanon-defaultnetworking-1/providers/Microsoft.Network/virtualNetworks/azne-vnet-roanon-t-1'
param userAssignedIdentities_azne_aks_dev_t_aahelp_1_agentpool_externalid string = '/subscriptions/d4655204-e89c-45ee-bd64-2705675e8513/resourceGroups/MC_azne-rg-roanon-t-aahelp_azne-aks-dev-t-aahelp-1_northeurope/providers/Microsoft.ManagedIdentity/userAssignedIdentities/azne-aks-dev-t-aahelp-1-agentpool'
param workspaces_DefaultWorkspace_d4655204_e89c_45ee_bd64_2705675e8513_NEU_externalid string = '/subscriptions/d4655204-e89c-45ee-bd64-2705675e8513/resourceGroups/DefaultResourceGroup-NEU/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-d4655204-e89c-45ee-bd64-2705675e8513-NEU'

resource managedClusters_azne_aks_dev_t_aahelp_1_name_resource 'Microsoft.ContainerService/managedClusters@2025-05-01' = {
  name: managedClusters_azne_aks_dev_t_aahelp_1_name
  location: 'northeurope'
  tags: {
    Application_Name: 'AAHELP'
    Application_Owner: 'Mike.coupes@TheAA.com'
    Cloud_Council_ID: 'CLOU0001219'
    Cost_Code: 'NA'
    Environment: 'Non-Production'
    Project: 'ROOTF'
    Region: 'NorthEurope'
    Review_Date: 'NA'
    Tower: 'NA'
    Tower_Unit: 'NA'
  }
  sku: {
    name: 'Base'
    tier: 'Free'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    kubernetesVersion: '1.32.7'
    dnsPrefix: '${managedClusters_azne_aks_dev_t_aahelp_1_name}-dns'
    agentPoolProfiles: [
      {
        name: 'agentpool'
        count: 2
        vmSize: 'Standard_D4ds_v5'
        osDiskSizeGB: 150
        osDiskType: 'Ephemeral'
        kubeletDiskType: 'OS'
        vnetSubnetID: '${virtualNetworks_azne_vnet_roanon_t_1_externalid}/subnets/azne-subn-roanon-t-aks-aahelp-1'
        maxPods: 110
        type: 'VirtualMachineScaleSets'
        maxCount: 5
        minCount: 2
        enableAutoScaling: true
        scaleDownMode: 'Delete'
        powerState: {
          code: 'Running'
        }
        orchestratorVersion: '1.32.7'
        enableNodePublicIP: false
        mode: 'System'
        osType: 'Linux'
        osSKU: 'Ubuntu'
        upgradeSettings: {
          maxSurge: '10%'
          undrainableNodeBehavior: 'Cordon'
          maxUnavailable: '0'
        }
        enableFIPS: false
        securityProfile: {
          enableVTPM: false
          enableSecureBoot: false
        }
      }
    ]
    windowsProfile: {
      adminUsername: 'azureuser'
      enableCSIProxy: true
    }
    servicePrincipalProfile: {
      clientId: 'msi'
    }
    addonProfiles: {
      azureKeyvaultSecretsProvider: {
        enabled: true
        config: {
          enableSecretRotation: 'true'
        }
      }
      azurepolicy: {
        enabled: true
      }
    }
    nodeResourceGroup: 'MC_azne-rg-roanon-t-aahelp_${managedClusters_azne_aks_dev_t_aahelp_1_name}_northeurope'
    enableRBAC: true
    supportPlan: 'KubernetesOfficial'
    networkProfile: {
      networkPlugin: 'azure'
      networkPolicy: 'azure'
      networkDataplane: 'azure'
      loadBalancerSku: 'Standard'
      loadBalancerProfile: {
        managedOutboundIPs: {
          count: 1
        }
        backendPoolType: 'nodeIPConfiguration'
      }
      serviceCidr: '172.16.30.0/24'
      dnsServiceIP: '172.16.30.10'
      outboundType: 'loadBalancer'
      serviceCidrs: [
        '172.16.30.0/24'
      ]
      ipFamilies: [
        'IPv4'
      ]
    }
    identityProfile: {
      kubeletidentity: {
        resourceId: userAssignedIdentities_azne_aks_dev_t_aahelp_1_agentpool_externalid
        clientId: '4d5aa81a-ef3a-4479-99a1-ab28c8fb919a'
        objectId: '0dee9e4a-0938-4581-b0ea-771862c0f2ef'
      }
    }
    autoScalerProfile: {
      'balance-similar-node-groups': 'false'
      'daemonset-eviction-for-empty-nodes': false
      'daemonset-eviction-for-occupied-nodes': true
      expander: 'random'
      'ignore-daemonsets-utilization': false
      'max-empty-bulk-delete': '10'
      'max-graceful-termination-sec': '600'
      'max-node-provision-time': '15m'
      'max-total-unready-percentage': '45'
      'new-pod-scale-up-delay': '0s'
      'ok-total-unready-count': '3'
      'scale-down-delay-after-add': '10m'
      'scale-down-delay-after-delete': '10s'
      'scale-down-delay-after-failure': '3m'
      'scale-down-unneeded-time': '10m'
      'scale-down-unready-time': '20m'
      'scale-down-utilization-threshold': '0.5'
      'scan-interval': '10s'
      'skip-nodes-with-local-storage': 'false'
      'skip-nodes-with-system-pods': 'true'
    }
    autoUpgradeProfile: {
      upgradeChannel: 'patch'
      nodeOSUpgradeChannel: 'NodeImage'
    }
    disableLocalAccounts: false
    securityProfile: {
      defender: {
        logAnalyticsWorkspaceResourceId: workspaces_DefaultWorkspace_d4655204_e89c_45ee_bd64_2705675e8513_NEU_externalid
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
      diskCSIDriver: {
        enabled: true
      }
      fileCSIDriver: {
        enabled: true
      }
      snapshotController: {
        enabled: true
      }
    }
    oidcIssuerProfile: {
      enabled: true
    }
    ingressProfile: {
      webAppRouting: {
        enabled: true
        nginx: {
          defaultIngressControllerType: 'AnnotationControlled'
        }
      }
    }
    workloadAutoScalerProfile: {}
    metricsProfile: {
      costAnalysis: {
        enabled: false
      }
    }
    nodeProvisioningProfile: {
      mode: 'Manual'
      defaultNodePools: 'Auto'
    }
    bootstrapProfile: {
      artifactSource: 'Direct'
    }
  }
}

resource managedClusters_azne_aks_dev_t_aahelp_1_name_agentpool 'Microsoft.ContainerService/managedClusters/agentPools@2025-05-01' = {
  parent: managedClusters_azne_aks_dev_t_aahelp_1_name_resource
  name: 'agentpool'
  properties: {
    count: 2
    vmSize: 'Standard_D4ds_v5'
    osDiskSizeGB: 150
    osDiskType: 'Ephemeral'
    kubeletDiskType: 'OS'
    vnetSubnetID: '${virtualNetworks_azne_vnet_roanon_t_1_externalid}/subnets/azne-subn-roanon-t-aks-aahelp-1'
    maxPods: 110
    type: 'VirtualMachineScaleSets'
    maxCount: 5
    minCount: 2
    enableAutoScaling: true
    scaleDownMode: 'Delete'
    powerState: {
      code: 'Running'
    }
    orchestratorVersion: '1.32.7'
    enableNodePublicIP: false
    mode: 'System'
    osType: 'Linux'
    osSKU: 'Ubuntu'
    upgradeSettings: {
      maxSurge: '10%'
      undrainableNodeBehavior: 'Cordon'
      maxUnavailable: '0'
    }
    enableFIPS: false
    securityProfile: {
      enableVTPM: false
      enableSecureBoot: false
    }
  }
}

resource managedClusters_azne_aks_dev_t_aahelp_1_name_aksManagedAutoUpgradeSchedule 'Microsoft.ContainerService/managedClusters/maintenanceConfigurations@2025-05-01' = {
  parent: managedClusters_azne_aks_dev_t_aahelp_1_name_resource
  name: 'aksManagedAutoUpgradeSchedule'
  properties: {
    maintenanceWindow: {
      schedule: {
        weekly: {
          intervalWeeks: 1
          dayOfWeek: 'Sunday'
        }
      }
      durationHours: 8
      utcOffset: '+00:00'
      startDate: '2025-08-30'
      startTime: '00:00'
    }
  }
}

resource managedClusters_azne_aks_dev_t_aahelp_1_name_aksManagedNodeOSUpgradeSchedule 'Microsoft.ContainerService/managedClusters/maintenanceConfigurations@2025-05-01' = {
  parent: managedClusters_azne_aks_dev_t_aahelp_1_name_resource
  name: 'aksManagedNodeOSUpgradeSchedule'
  properties: {
    maintenanceWindow: {
      schedule: {
        weekly: {
          intervalWeeks: 1
          dayOfWeek: 'Sunday'
        }
      }
      durationHours: 8
      utcOffset: '+00:00'
      startDate: '2025-08-30'
      startTime: '00:00'
    }
  }
}

resource managedClusters_azne_aks_dev_t_aahelp_1_name_defender_cloudposture 'Microsoft.ContainerService/managedClusters/trustedAccessRoleBindings@2025-05-01' = {
  parent: managedClusters_azne_aks_dev_t_aahelp_1_name_resource
  name: 'defender-cloudposture'
  properties: {
    sourceResourceId: '/subscriptions/d4655204-e89c-45ee-bd64-2705675e8513/providers/Microsoft.Security/pricings/CloudPosture/securityOperators/DefenderCSPMSecurityOperator'
    roles: [
      'Microsoft.Security/pricings/microsoft-defender-operator'
    ]
  }
}

resource managedClusters_azne_aks_dev_t_aahelp_1_name_policymgmt1_containers 'Microsoft.ContainerService/managedClusters/trustedAccessRoleBindings@2025-05-01' = {
  parent: managedClusters_azne_aks_dev_t_aahelp_1_name_resource
  name: 'policymgmt1-containers'
  properties: {
    sourceResourceId: '/subscriptions/d4655204-e89c-45ee-bd64-2705675e8513/providers/Microsoft.Security/pricings/Containers/securityOperators/DefenderForContainersSecurityOperator'
    roles: [
      'Microsoft.Security/pricings/microsoft-defender-policy-operator'
    ]
  }
}

resource managedClusters_azne_aks_dev_t_aahelp_1_name_agentpool_aks_agentpool_15566196_vmss000001 'Microsoft.ContainerService/managedClusters/agentPools/machines@2025-04-02-preview' = {
  parent: managedClusters_azne_aks_dev_t_aahelp_1_name_agentpool
  name: 'aks-agentpool-15566196-vmss000001'
  properties: {
    network: {}
  }
  dependsOn: [
    managedClusters_azne_aks_dev_t_aahelp_1_name_resource
  ]
}

resource managedClusters_azne_aks_dev_t_aahelp_1_name_agentpool_aks_agentpool_15566196_vmss000002 'Microsoft.ContainerService/managedClusters/agentPools/machines@2025-04-02-preview' = {
  parent: managedClusters_azne_aks_dev_t_aahelp_1_name_agentpool
  name: 'aks-agentpool-15566196-vmss000002'
  properties: {
    network: {}
  }
  dependsOn: [
    managedClusters_azne_aks_dev_t_aahelp_1_name_resource
  ]
}
