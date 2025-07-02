# 17_multi_cloud_deployment

## 概要

複数のクラウドプロバイダー（AWS、GCP、Azure）にまたがるアプリケーション展開を実装し、ベンダーロックイン回避、地理的冗長性、コスト最適化を実現します。

## 目的

- マルチクラウド戦略の実装
- クロスクラウドネットワーキング
- 統一されたデプロイメントパイプライン
- クラウド間のデータ同期とレプリケーション

## アーキテクチャ

```
┌──────────────────────────────────────────┐
│         Global Load Balancer             │
│      (CloudFlare / Route53 / ...)        │
└────────────┬─────────────┬───────────────┘
             │             │
    ┌────────▼────┐  ┌─────▼────┐  ┌────────┐
    │    AWS      │  │   GCP    │  │ Azure  │
    │  Region     │  │  Region  │  │ Region │
    │             │  │          │  │        │
    │ ┌─────────┐ │  │ ┌──────┐ │  │ ┌────┐ │
    │ │   EKS   │ │  │ │ GKE  │ │  │ │AKS │ │
    │ │ Cluster │ │  │ │Cluster│ │  │ │    │ │
    │ └─────────┘ │  │ └──────┘ │  │ └────┘ │
    │             │  │          │  │        │
    │ ┌─────────┐ │  │ ┌──────┐ │  │ ┌────┐ │
    │ │   RDS   │ │  │ │Cloud │ │  │ │SQL │ │
    │ │ Aurora  │ │  │ │ SQL  │ │  │ │ DB │ │
    │ └─────────┘ │  │ └──────┘ │  │ └────┘ │
    └─────────────┘  └──────────┘  └────────┘
           │              │             │
           └──────────────┼─────────────┘
                          │
                [VPN / Interconnect]
```

## 検証項目

### 1. クラウド抽象化レイヤー
- **統一API**: Terraform/Pulumi
- **コンテナランタイム**: 共通Kubernetes
- **サービスメッシュ**: Istio Multi-cluster
- **CI/CD**: GitOps with ArgoCD

### 2. ネットワーク接続性
- **VPN接続**: Site-to-Site VPN
- **専用接続**: Direct Connect/Interconnect
- **SDN**: Software Defined Networking
- **グローバルロードバランシング**: Anycast

### 3. データ管理
- **マルチマスターレプリケーション**: CockroachDB
- **オブジェクトストレージ同期**: MinIO
- **CDN**: マルチクラウドCDN
- **バックアップ**: クロスクラウドバックアップ

### 4. セキュリティとコンプライアンス
- **統一認証**: OIDC/SAML
- **シークレット管理**: HashiCorp Vault
- **コンプライアンス**: SOC2, GDPR
- **暗号化**: End-to-End暗号化

## TDDアプローチ

### Red Phase (マルチクラウドデプロイメントのテスト)
```javascript
// test/multi-cloud-deployment.test.js
const { CloudProviderFactory } = require('./cloud-providers');
const { expect } = require('chai');

describe('Multi-Cloud Deployment', () => {
  let providers;
  let deploymentManager;
  
  beforeAll(async () => {
    // 各クラウドプロバイダーの初期化
    providers = {
      aws: CloudProviderFactory.create('aws', {
        region: 'us-east-1',
        credentials: process.env.AWS_CREDENTIALS
      }),
      gcp: CloudProviderFactory.create('gcp', {
        region: 'us-central1',
        project: process.env.GCP_PROJECT
      }),
      azure: CloudProviderFactory.create('azure', {
        region: 'eastus',
        subscription: process.env.AZURE_SUBSCRIPTION
      })
    };
    
    deploymentManager = new MultiCloudDeploymentManager(providers);
  });

  it('should deploy Kubernetes clusters across all clouds', async () => {
    const clusterConfig = {
      name: 'multi-cloud-poc',
      version: '1.28',
      nodeCount: 3,
      nodeType: 'standard',
      networking: {
        podCidr: '10.0.0.0/16',
        serviceCidr: '10.1.0.0/16'
      }
    };
    
    // 並列デプロイメント
    const deployments = await Promise.all([
      providers.aws.deployEKS(clusterConfig),
      providers.gcp.deployGKE(clusterConfig),
      providers.azure.deployAKS(clusterConfig)
    ]);
    
    // クラスターの健全性確認
    for (const deployment of deployments) {
      expect(deployment.status).to.equal('ready');
      expect(deployment.nodeCount).to.equal(3);
      
      // クラスターへの接続確認
      const client = await deployment.getKubernetesClient();
      const nodes = await client.listNodes();
      
      expect(nodes.length).to.equal(3);
      nodes.forEach(node => {
        expect(node.status).to.equal('Ready');
      });
    }
    
    // クロスクラウドネットワーキングの設定
    await deploymentManager.setupInterCloudNetworking(deployments);
    
    // 接続性テスト
    const connectivityTest = await deploymentManager.testInterCloudConnectivity();
    expect(connectivityTest.allConnected).to.be.true;
    
    connectivityTest.results.forEach(result => {
      expect(result.latency).to.be.lessThan(100); // 100ms以下
      expect(result.packetLoss).to.equal(0);
    });
  });

  it('should deploy unified application across clouds', async () => {
    const appConfig = {
      name: 'global-web-app',
      image: 'webapp:v1.0',
      replicas: {
        aws: 3,
        gcp: 3,
        azure: 2
      },
      resources: {
        cpu: '500m',
        memory: '1Gi'
      },
      env: {
        CLOUD_PROVIDER: '${CLOUD_PROVIDER}',
        REGION: '${REGION}',
        CLUSTER_NAME: '${CLUSTER_NAME}'
      }
    };
    
    // ArgoCD アプリケーション定義
    const argoCDApp = {
      apiVersion: 'argoproj.io/v1alpha1',
      kind: 'ApplicationSet',
      metadata: {
        name: 'multi-cloud-app',
        namespace: 'argocd'
      },
      spec: {
        generators: [{
          list: {
            elements: [
              { cluster: 'aws-cluster', url: providers.aws.clusterEndpoint },
              { cluster: 'gcp-cluster', url: providers.gcp.clusterEndpoint },
              { cluster: 'azure-cluster', url: providers.azure.clusterEndpoint }
            ]
          }
        }],
        template: {
          metadata: {
            name: '{{cluster}}-app'
          },
          spec: {
            project: 'default',
            source: {
              repoURL: 'https://github.com/org/multi-cloud-app',
              targetRevision: 'HEAD',
              path: 'manifests/{{cluster}}'
            },
            destination: {
              server: '{{url}}'
            },
            syncPolicy: {
              automated: {
                prune: true,
                selfHeal: true
              }
            }
          }
        }
      }
    };
    
    // ArgoCDを使用したデプロイ
    await deploymentManager.deployWithArgoCD(argoCDApp);
    
    // デプロイメント確認
    const deploymentStatus = await deploymentManager.waitForDeployment(
      'global-web-app',
      300000 // 5分
    );
    
    expect(deploymentStatus.aws.ready).to.be.true;
    expect(deploymentStatus.gcp.ready).to.be.true;
    expect(deploymentStatus.azure.ready).to.be.true;
    
    // エンドポイントの取得
    const endpoints = await deploymentManager.getApplicationEndpoints('global-web-app');
    
    // 各エンドポイントへのヘルスチェック
    for (const [cloud, endpoint] of Object.entries(endpoints)) {
      const response = await fetch(`${endpoint}/health`);
      expect(response.status).to.equal(200);
      
      const health = await response.json();
      expect(health.cloud).to.equal(cloud);
      expect(health.status).to.equal('healthy');
    }
  });

  it('should implement global load balancing', async () => {
    // Cloudflare Load Balancerの設定
    const loadBalancerConfig = {
      name: 'global-lb',
      domain: 'app.multicloud.example.com',
      pools: [
        {
          name: 'aws-pool',
          origins: [
            { address: endpoints.aws, weight: 1 }
          ],
          monitor: '/health',
          region: 'Americas'
        },
        {
          name: 'gcp-pool',
          origins: [
            { address: endpoints.gcp, weight: 1 }
          ],
          monitor: '/health',
          region: 'Asia-Pacific'
        },
        {
          name: 'azure-pool',
          origins: [
            { address: endpoints.azure, weight: 1 }
          ],
          monitor: '/health',
          region: 'Europe'
        }
      ],
      steering: {
        policy: 'geo',
        fallbackPool: 'aws-pool'
      }
    };
    
    const lb = await deploymentManager.createGlobalLoadBalancer(loadBalancerConfig);
    
    // 地理的ルーティングのテスト
    const geoTests = [
      { location: 'New York', expectedPool: 'aws-pool' },
      { location: 'Tokyo', expectedPool: 'gcp-pool' },
      { location: 'London', expectedPool: 'azure-pool' }
    ];
    
    for (const test of geoTests) {
      const response = await simulateRequestFromLocation(
        `https://${loadBalancerConfig.domain}`,
        test.location
      );
      
      expect(response.headers['x-served-by']).to.include(test.expectedPool);
      expect(response.status).to.equal(200);
    }
    
    // フェイルオーバーテスト
    await providers.aws.simulateOutage();
    
    // Americas からのリクエストが GCP にフェイルオーバー
    const failoverResponse = await simulateRequestFromLocation(
      `https://${loadBalancerConfig.domain}`,
      'New York'
    );
    
    expect(failoverResponse.headers['x-served-by']).to.include('gcp-pool');
  });

  it('should synchronize data across clouds', async () => {
    // CockroachDB マルチリージョンクラスター
    const dbConfig = {
      name: 'global-database',
      nodes: [
        { cloud: 'aws', region: 'us-east-1', count: 3 },
        { cloud: 'gcp', region: 'us-central1', count: 3 },
        { cloud: 'azure', region: 'eastus', count: 3 }
      ],
      replicationFactor: 5,
      survivalGoal: 'region',
      backupSchedule: '0 2 * * *'
    };
    
    const database = await deploymentManager.deployCockroachDB(dbConfig);
    
    // データ書き込みテスト（AWS）
    const awsClient = await database.getClient('aws');
    await awsClient.query(`
      INSERT INTO users (id, name, email, region)
      VALUES ($1, $2, $3, $4)
    `, ['user-1', 'Alice', 'alice@example.com', 'us-east-1']);
    
    // 他のリージョンでの読み取り確認
    const gcpClient = await database.getClient('gcp');
    const result = await gcpClient.query(
      'SELECT * FROM users WHERE id = $1',
      ['user-1']
    );
    
    expect(result.rows[0].name).to.equal('Alice');
    
    // レプリケーションラグの測定
    const replicationLag = await database.measureReplicationLag();
    
    Object.entries(replicationLag).forEach(([region, lag]) => {
      expect(lag).to.be.lessThan(1000); // 1秒以内
    });
    
    // リージョン障害シミュレーション
    await providers.aws.simulateRegionFailure();
    
    // 他のリージョンで書き込みが継続可能
    const azureClient = await database.getClient('azure');
    await azureClient.query(`
      INSERT INTO users (id, name, email, region)
      VALUES ($1, $2, $3, $4)
    `, ['user-2', 'Bob', 'bob@example.com', 'eastus']);
    
    // クォーラムが維持されていることを確認
    const clusterStatus = await database.getClusterStatus();
    expect(clusterStatus.healthy).to.be.true;
    expect(clusterStatus.availableNodes).to.be.at.least(5);
  });

  it('should implement unified CI/CD pipeline', async () => {
    // Terraform によるインフラストラクチャ定義
    const terraformConfig = `
      module "aws_infrastructure" {
        source = "./modules/aws"
        region = var.aws_region
        cluster_name = var.cluster_name
      }
      
      module "gcp_infrastructure" {
        source = "./modules/gcp"
        region = var.gcp_region
        project = var.gcp_project
        cluster_name = var.cluster_name
      }
      
      module "azure_infrastructure" {
        source = "./modules/azure"
        region = var.azure_region
        subscription = var.azure_subscription
        cluster_name = var.cluster_name
      }
      
      module "networking" {
        source = "./modules/multi-cloud-networking"
        aws_vpc = module.aws_infrastructure.vpc_id
        gcp_network = module.gcp_infrastructure.network_id
        azure_vnet = module.azure_infrastructure.vnet_id
      }
    `;
    
    // GitHub Actions ワークフロー
    const githubWorkflow = {
      name: 'Multi-Cloud Deploy',
      on: {
        push: {
          branches: ['main']
        }
      },
      jobs: {
        deploy: {
          'runs-on': 'ubuntu-latest',
          steps: [
            {
              name: 'Checkout',
              uses: 'actions/checkout@v3'
            },
            {
              name: 'Setup Terraform',
              uses: 'hashicorp/setup-terraform@v2'
            },
            {
              name: 'Terraform Init',
              run: 'terraform init'
            },
            {
              name: 'Terraform Plan',
              run: 'terraform plan -out=tfplan'
            },
            {
              name: 'Terraform Apply',
              run: 'terraform apply -auto-approve tfplan'
            },
            {
              name: 'Deploy Applications',
              run: `
                argocd app create multi-cloud-app \
                  --repo ${{ github.repository }} \
                  --path manifests \
                  --dest-server https://kubernetes.default.svc \
                  --sync-policy automated
              `
            }
          ]
        }
      }
    };
    
    // パイプライン実行
    const pipelineRun = await deploymentManager.triggerPipeline({
      workflow: githubWorkflow,
      branch: 'feature/update-app',
      commit: 'feat: Add new feature'
    });
    
    // パイプライン完了待機
    await pipelineRun.waitForCompletion();
    
    expect(pipelineRun.status).to.equal('success');
    expect(pipelineRun.stages.terraform.status).to.equal('success');
    expect(pipelineRun.stages.argocd.status).to.equal('success');
    
    // 全クラウドでの更新確認
    const deploymentVersions = await deploymentManager.getDeployedVersions();
    
    Object.values(deploymentVersions).forEach(version => {
      expect(version).to.include('feature/update-app');
    });
  });

  it('should manage costs across clouds', async () => {
    // コスト監視の設定
    const costManager = new MultiCloudCostManager({
      aws: { accountId: process.env.AWS_ACCOUNT },
      gcp: { projectId: process.env.GCP_PROJECT },
      azure: { subscriptionId: process.env.AZURE_SUBSCRIPTION }
    });
    
    // 現在のコスト取得
    const currentCosts = await costManager.getCurrentMonthCosts();
    
    console.log('Current month costs:');
    console.log(`AWS: $${currentCosts.aws.total}`);
    console.log(`GCP: $${currentCosts.gcp.total}`);
    console.log(`Azure: $${currentCosts.azure.total}`);
    console.log(`Total: $${currentCosts.total}`);
    
    // コスト最適化の推奨事項
    const recommendations = await costManager.getOptimizationRecommendations();
    
    expect(recommendations).to.have.length.greaterThan(0);
    
    // 自動スケーリングポリシーの調整
    if (currentCosts.total > 1000) { // $1000を超えた場合
      await deploymentManager.applyCoastOptimizations({
        scaleDown: {
          aws: { minNodes: 2, maxNodes: 5 },
          gcp: { minNodes: 2, maxNodes: 5 },
          azure: { minNodes: 1, maxNodes: 3 }
        },
        spotInstances: {
          enabled: true,
          percentage: 50
        }
      });
    }
    
    // 予算アラートの設定
    await costManager.setBudgetAlerts({
      monthly: 5000,
      alerts: [
        { threshold: 0.8, action: 'email' },
        { threshold: 0.9, action: 'slack' },
        { threshold: 1.0, action: 'pagerduty' }
      ]
    });
  });
});

// セキュリティとコンプライアンステスト
describe('Multi-Cloud Security', () => {
  it('should implement unified authentication', async () => {
    // HashiCorp Vault の設定
    const vaultConfig = {
      backends: {
        aws: { type: 'aws', role: 'multi-cloud-role' },
        gcp: { type: 'gcp', role: 'multi-cloud-sa' },
        azure: { type: 'azure', role: 'multi-cloud-sp' }
      },
      policies: {
        'multi-cloud-policy': {
          path: {
            'secret/data/multi-cloud/*': {
              capabilities: ['read', 'list']
            }
          }
        }
      }
    };
    
    const vault = await deploymentManager.setupVault(vaultConfig);
    
    // 統一認証のテスト
    const token = await vault.authenticate({
      method: 'oidc',
      provider: 'okta'
    });
    
    // 各クラウドのシークレット取得
    const secrets = await vault.getSecrets(token, 'multi-cloud/*');
    
    expect(secrets).to.have.property('aws-access-key');
    expect(secrets).to.have.property('gcp-service-account');
    expect(secrets).to.have.property('azure-client-secret');
    
    // 動的シークレット生成
    const dynamicCreds = await vault.generateDynamicCredentials(token, {
      aws: { ttl: '1h', policy: 'read-only' },
      gcp: { ttl: '1h', scopes: ['compute.readonly'] },
      azure: { ttl: '1h', role: 'Reader' }
    });
    
    // 生成されたクレデンシャルの検証
    Object.entries(dynamicCreds).forEach(([cloud, creds]) => {
      expect(creds).to.have.property('expiry');
      expect(new Date(creds.expiry)).to.be.greaterThan(new Date());
    });
  });
});
```

### Green Phase (マルチクラウド実装)
```javascript
// multi-cloud-manager.js
const { TerraformCloud } = require('@cdktf/provider-terraform-cloud');
const { App, TerraformStack } = require('cdktf');

class MultiCloudDeploymentManager {
  constructor(providers) {
    this.providers = providers;
    this.clusters = new Map();
    this.applications = new Map();
  }
  
  async deployInfrastructure(config) {
    const app = new App();
    const stack = new TerraformStack(app, 'multi-cloud-stack');
    
    // AWS Infrastructure
    const awsResources = await this.deployAWSResources(stack, config.aws);
    
    // GCP Infrastructure
    const gcpResources = await this.deployGCPResources(stack, config.gcp);
    
    // Azure Infrastructure
    const azureResources = await this.deployAzureResources(stack, config.azure);
    
    // Cross-cloud networking
    await this.setupNetworking(stack, {
      aws: awsResources,
      gcp: gcpResources,
      azure: azureResources
    });
    
    // Synthesize and deploy
    app.synth();
    
    return {
      aws: awsResources,
      gcp: gcpResources,
      azure: azureResources
    };
  }
  
  async deployAWSResources(stack, config) {
    const vpc = new aws.Vpc(stack, 'aws-vpc', {
      cidrBlock: '10.0.0.0/16',
      enableDnsHostnames: true,
      enableDnsSupport: true
    });
    
    const eksCluster = new aws.EksCluster(stack, 'aws-eks', {
      name: config.clusterName,
      version: config.kubernetesVersion,
      roleArn: config.eksRole,
      vpcConfig: {
        subnetIds: vpc.privateSubnets.map(s => s.id),
        securityGroupIds: [vpc.defaultSecurityGroup.id]
      }
    });
    
    const nodeGroup = new aws.EksNodeGroup(stack, 'aws-node-group', {
      clusterName: eksCluster.name,
      nodeGroupName: 'workers',
      subnetsIds: vpc.privateSubnets.map(s => s.id),
      scalingConfig: {
        desiredSize: config.nodeCount,
        maxSize: config.maxNodes,
        minSize: config.minNodes
      },
      instanceTypes: [config.instanceType]
    });
    
    return {
      vpc,
      cluster: eksCluster,
      nodeGroup,
      endpoint: eksCluster.endpoint,
      certificateAuthority: eksCluster.certificateAuthority
    };
  }
  
  async deployGCPResources(stack, config) {
    const network = new gcp.ComputeNetwork(stack, 'gcp-network', {
      name: config.networkName,
      autoCreateSubnetworks: false
    });
    
    const subnet = new gcp.ComputeSubnetwork(stack, 'gcp-subnet', {
      name: config.subnetName,
      network: network.selfLink,
      ipCidrRange: '10.1.0.0/16',
      region: config.region
    });
    
    const gkeCluster = new gcp.ContainerCluster(stack, 'gcp-gke', {
      name: config.clusterName,
      location: config.region,
      initialNodeCount: 1,
      removeDefaultNodePool: true,
      network: network.name,
      subnetwork: subnet.name,
      ipAllocationPolicy: {
        clusterIpv4CidrBlock: '10.2.0.0/16',
        servicesIpv4CidrBlock: '10.3.0.0/16'
      }
    });
    
    const nodePool = new gcp.ContainerNodePool(stack, 'gcp-node-pool', {
      name: 'workers',
      cluster: gkeCluster.name,
      location: config.region,
      nodeCount: config.nodeCount,
      nodeConfig: {
        machineType: config.machineType,
        oauthScopes: [
          'https://www.googleapis.com/auth/cloud-platform'
        ]
      },
      autoscaling: {
        minNodeCount: config.minNodes,
        maxNodeCount: config.maxNodes
      }
    });
    
    return {
      network,
      subnet,
      cluster: gkeCluster,
      nodePool,
      endpoint: gkeCluster.endpoint,
      masterAuth: gkeCluster.masterAuth
    };
  }
  
  async deployAzureResources(stack, config) {
    const resourceGroup = new azure.ResourceGroup(stack, 'azure-rg', {
      name: config.resourceGroupName,
      location: config.location
    });
    
    const vnet = new azure.VirtualNetwork(stack, 'azure-vnet', {
      name: config.vnetName,
      resourceGroupName: resourceGroup.name,
      location: resourceGroup.location,
      addressSpace: {
        addressPrefixes: ['10.4.0.0/16']
      }
    });
    
    const subnet = new azure.Subnet(stack, 'azure-subnet', {
      name: config.subnetName,
      resourceGroupName: resourceGroup.name,
      virtualNetworkName: vnet.name,
      addressPrefixes: ['10.4.1.0/24']
    });
    
    const aksCluster = new azure.KubernetesCluster(stack, 'azure-aks', {
      name: config.clusterName,
      location: resourceGroup.location,
      resourceGroupName: resourceGroup.name,
      kubernetesVersion: config.kubernetesVersion,
      defaultNodePool: {
        name: 'default',
        nodeCount: config.nodeCount,
        vmSize: config.vmSize,
        vnetSubnetId: subnet.id
      },
      identity: {
        type: 'SystemAssigned'
      },
      networkProfile: {
        networkPlugin: 'azure',
        serviceCidr: '10.5.0.0/16',
        dnsServiceIp: '10.5.0.10'
      }
    });
    
    return {
      resourceGroup,
      vnet,
      subnet,
      cluster: aksCluster,
      endpoint: aksCluster.kubeConfig[0].host,
      kubeConfig: aksCluster.kubeConfigRaw
    };
  }
  
  async setupNetworking(stack, resources) {
    // AWS to GCP VPN
    const awsGcpVpn = new VPNConnection(stack, 'aws-gcp-vpn', {
      aws: {
        vpc: resources.aws.vpc,
        customerGateway: resources.gcp.vpnGateway
      },
      gcp: {
        network: resources.gcp.network,
        vpnGateway: resources.aws.customerGateway
      }
    });
    
    // AWS to Azure VPN
    const awsAzureVpn = new VPNConnection(stack, 'aws-azure-vpn', {
      aws: {
        vpc: resources.aws.vpc,
        customerGateway: resources.azure.vpnGateway
      },
      azure: {
        vnet: resources.azure.vnet,
        vpnGateway: resources.aws.customerGateway
      }
    });
    
    // GCP to Azure Private Peering
    const gcpAzurePeering = new NetworkPeering(stack, 'gcp-azure-peering', {
      gcp: {
        network: resources.gcp.network
      },
      azure: {
        vnet: resources.azure.vnet
      }
    });
    
    // Route tables
    await this.configureRouting(stack, resources);
  }
  
  async setupInterCloudNetworking(clusters) {
    // Istio multi-cluster setup
    const istioConfig = {
      version: '1.18.0',
      meshId: 'multi-cloud-mesh',
      network: 'multi-cloud-network',
      clusters: clusters.map(c => ({
        name: c.name,
        endpoint: c.endpoint,
        network: c.cloud
      }))
    };
    
    // Install Istio on each cluster
    for (const cluster of clusters) {
      await this.installIstio(cluster, istioConfig);
    }
    
    // Configure multi-cluster mesh
    await this.configureMultiClusterMesh(clusters, istioConfig);
    
    // Test connectivity
    return this.testMeshConnectivity(clusters);
  }
  
  async installIstio(cluster, config) {
    const istioctl = new IstioctlClient(cluster.kubeconfig);
    
    await istioctl.install({
      profile: 'default',
      values: {
        global: {
          meshID: config.meshId,
          multiCluster: {
            clusterName: cluster.name
          },
          network: cluster.cloud
        }
      }
    });
    
    // Enable sidecar injection
    await cluster.kubectl('label namespace default istio-injection=enabled');
  }
  
  async deployApplication(appConfig) {
    const deployments = [];
    
    for (const [cloud, config] of Object.entries(appConfig.clouds)) {
      const deployment = {
        cloud,
        manifest: this.generateManifest(appConfig, cloud, config),
        cluster: this.clusters.get(cloud)
      };
      
      deployments.push(deployment);
    }
    
    // Deploy using ArgoCD
    const argoApp = await this.createArgoApplication(appConfig, deployments);
    
    // Wait for sync
    await this.waitForArgoSync(argoApp);
    
    return {
      application: argoApp,
      deployments
    };
  }
  
  generateManifest(appConfig, cloud, cloudConfig) {
    return {
      apiVersion: 'apps/v1',
      kind: 'Deployment',
      metadata: {
        name: appConfig.name,
        labels: {
          app: appConfig.name,
          cloud: cloud,
          version: appConfig.version
        }
      },
      spec: {
        replicas: cloudConfig.replicas,
        selector: {
          matchLabels: {
            app: appConfig.name,
            cloud: cloud
          }
        },
        template: {
          metadata: {
            labels: {
              app: appConfig.name,
              cloud: cloud,
              version: appConfig.version
            }
          },
          spec: {
            containers: [{
              name: appConfig.name,
              image: appConfig.image,
              ports: appConfig.ports,
              env: [
                { name: 'CLOUD_PROVIDER', value: cloud },
                { name: 'REGION', value: cloudConfig.region },
                { name: 'CLUSTER_NAME', value: cloudConfig.clusterName },
                ...this.interpolateEnvVars(appConfig.env, cloudConfig)
              ],
              resources: appConfig.resources
            }]
          }
        }
      }
    };
  }
  
  async createGlobalLoadBalancer(config) {
    // Cloudflare Load Balancer
    const cf = new CloudflareClient({
      apiToken: process.env.CLOUDFLARE_API_TOKEN
    });
    
    // Create pools
    const pools = await Promise.all(
      config.pools.map(pool => 
        cf.createPool({
          name: pool.name,
          origins: pool.origins,
          checkRegions: ['WNAM', 'ENAM', 'WEU', 'EEU', 'SEAS', 'NEAS'],
          monitor: pool.monitor
        })
      )
    );
    
    // Create load balancer
    const loadBalancer = await cf.createLoadBalancer({
      name: config.name,
      fallbackPool: pools.find(p => p.name === config.steering.fallbackPool).id,
      defaultPools: pools.map(p => p.id),
      regionPools: Object.fromEntries(
        pools.map(p => [p.region, [p.id]])
      ),
      proxied: true,
      steeringPolicy: config.steering.policy
    });
    
    // Create DNS record
    await cf.createDNSRecord({
      type: 'CNAME',
      name: config.domain.split('.')[0],
      content: loadBalancer.hostname,
      proxied: true
    });
    
    return loadBalancer;
  }
  
  async deployCockroachDB(config) {
    const crdb = new CockroachDBCluster(config);
    
    // Deploy nodes across clouds
    const nodes = [];
    
    for (const nodeConfig of config.nodes) {
      const provider = this.providers[nodeConfig.cloud];
      const instances = await provider.deployInstances({
        count: nodeConfig.count,
        type: 'n2-standard-8',
        region: nodeConfig.region,
        userData: crdb.getNodeInitScript(nodeConfig)
      });
      
      nodes.push(...instances);
    }
    
    // Initialize cluster
    await crdb.initializeCluster(nodes);
    
    // Configure regions
    await crdb.configureRegions(config.nodes);
    
    // Set up backups
    await crdb.configureBackups({
      schedule: config.backupSchedule,
      destinations: {
        aws: 's3://multi-cloud-backups/cockroachdb',
        gcp: 'gs://multi-cloud-backups/cockroachdb',
        azure: 'https://multicloudbackups.blob.core.windows.net/cockroachdb'
      }
    });
    
    return crdb;
  }
}

// クラウドプロバイダー抽象化
class CloudProvider {
  constructor(name, config) {
    this.name = name;
    this.config = config;
  }
  
  async deployKubernetesCluster(config) {
    throw new Error('Must be implemented by subclass');
  }
  
  async getKubernetesClient() {
    throw new Error('Must be implemented by subclass');
  }
  
  async deployInstances(config) {
    throw new Error('Must be implemented by subclass');
  }
}

class AWSProvider extends CloudProvider {
  constructor(config) {
    super('aws', config);
    this.eks = new AWS.EKS({ region: config.region });
    this.ec2 = new AWS.EC2({ region: config.region });
  }
  
  async deployEKS(config) {
    // EKS cluster creation
    const cluster = await this.eks.createCluster({
      name: config.name,
      version: config.version,
      roleArn: this.config.eksRole,
      resourcesVpcConfig: {
        subnetIds: await this.getSubnetIds()
      }
    }).promise();
    
    // Wait for cluster to be active
    await this.waitForClusterActive(cluster.cluster.name);
    
    // Create node group
    await this.createNodeGroup(cluster.cluster.name, config);
    
    return {
      name: cluster.cluster.name,
      endpoint: cluster.cluster.endpoint,
      status: 'ready',
      cloud: 'aws'
    };
  }
  
  async getKubernetesClient() {
    const cluster = await this.eks.describeCluster({
      name: this.config.clusterName
    }).promise();
    
    const kubeconfig = this.generateKubeconfig(cluster.cluster);
    
    return new KubernetesClient(kubeconfig);
  }
}

class GCPProvider extends CloudProvider {
  constructor(config) {
    super('gcp', config);
    this.container = new ContainerClient({
      projectId: config.project,
      keyFilename: config.keyFile
    });
  }
  
  async deployGKE(config) {
    const cluster = await this.container.createCluster({
      cluster: {
        name: config.name,
        initialNodeCount: config.nodeCount,
        masterAuth: {
          clientCertificateConfig: {}
        }
      },
      parent: `projects/${this.config.project}/locations/${this.config.region}`
    });
    
    // Wait for operation to complete
    await this.waitForOperation(cluster.name);
    
    return {
      name: config.name,
      endpoint: cluster.endpoint,
      status: 'ready',
      cloud: 'gcp'
    };
  }
}

class AzureProvider extends CloudProvider {
  constructor(config) {
    super('azure', config);
    this.containerService = new ContainerServiceClient(
      config.credentials,
      config.subscription
    );
  }
  
  async deployAKS(config) {
    const cluster = await this.containerService.managedClusters.beginCreateOrUpdate(
      config.resourceGroup,
      config.name,
      {
        location: this.config.region,
        kubernetesVersion: config.version,
        agentPoolProfiles: [{
          name: 'nodepool1',
          count: config.nodeCount,
          vmSize: 'Standard_DS2_v2'
        }]
      }
    );
    
    await cluster.pollUntilFinished();
    
    return {
      name: config.name,
      endpoint: cluster.fqdn,
      status: 'ready',
      cloud: 'azure'
    };
  }
}

export {
  MultiCloudDeploymentManager,
};

export const CloudProviderFactory = {
  create(type: string, config: any) {
    switch (type) {
      case 'aws':
        return new AWSProvider(config);
      case 'gcp':
        return new GCPProvider(config);
      case 'azure':
        return new AzureProvider(config);
      default:
        throw new Error(`Unknown cloud provider: ${type}`);
    }
  }
};
```

### Terraform設定
```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  
  backend "s3" {
    bucket = "multi-cloud-terraform-state"
    key    = "global/terraform.tfstate"
    region = "us-east-1"
  }
}

# AWS Provider
provider "aws" {
  region = var.aws_region
}

# GCP Provider
provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
}

# Azure Provider
provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription
}

# Multi-Cloud VPN Module
module "multi_cloud_vpn" {
  source = "./modules/multi-cloud-vpn"
  
  aws_vpc_id        = module.aws.vpc_id
  gcp_network_name  = module.gcp.network_name
  azure_vnet_id     = module.azure.vnet_id
}

# Global Load Balancer
resource "cloudflare_load_balancer" "global" {
  zone_id = var.cloudflare_zone_id
  name    = "multi-cloud-lb"
  
  default_pool_ids = [
    cloudflare_load_balancer_pool.aws.id,
    cloudflare_load_balancer_pool.gcp.id,
    cloudflare_load_balancer_pool.azure.id
  ]
  
  fallback_pool_id = cloudflare_load_balancer_pool.aws.id
  
  steering_policy = "geo"
  
  region_pools {
    region   = "WNAM"
    pool_ids = [cloudflare_load_balancer_pool.aws.id]
  }
  
  region_pools {
    region   = "SEAS"
    pool_ids = [cloudflare_load_balancer_pool.gcp.id]
  }
  
  region_pools {
    region   = "WEU"
    pool_ids = [cloudflare_load_balancer_pool.azure.id]
  }
}
```

### ArgoCD ApplicationSet
```yaml
# argocd/multi-cloud-appset.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: multi-cloud-apps
  namespace: argocd
spec:
  generators:
  - matrix:
      generators:
      - git:
          repoURL: https://github.com/org/multi-cloud-apps
          revision: HEAD
          directories:
          - path: apps/*
      - list:
          elements:
          - cluster: aws-prod
            url: https://k8s-aws.example.com
            cloud: aws
          - cluster: gcp-prod
            url: https://k8s-gcp.example.com
            cloud: gcp
          - cluster: azure-prod
            url: https://k8s-azure.example.com
            cloud: azure
  template:
    metadata:
      name: '{{path.basename}}-{{cluster}}'
    spec:
      project: multi-cloud
      source:
        repoURL: https://github.com/org/multi-cloud-apps
        targetRevision: HEAD
        path: '{{path}}'
        helm:
          valueFiles:
          - values-{{cloud}}.yaml
          parameters:
          - name: cloud.provider
            value: '{{cloud}}'
          - name: cloud.cluster
            value: '{{cluster}}'
      destination:
        server: '{{url}}'
        namespace: '{{path.basename}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
        - CreateNamespace=true
```

## 実行と検証

### 1. インフラストラクチャのプロビジョニング
```bash
# Terraform初期化
terraform init

# プラン確認
terraform plan -out=tfplan

# 適用
terraform apply tfplan
```

### 2. Kubernetesクラスターの確認
```bash
# コンテキストの追加
aws eks update-kubeconfig --name multi-cloud-poc --region us-east-1
gcloud container clusters get-credentials multi-cloud-poc --region us-central1
az aks get-credentials --name multi-cloud-poc --resource-group multi-cloud-rg

# クラスター確認
kubectl config get-contexts
```

### 3. アプリケーションのデプロイ
```bash
# ArgoCD インストール
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# ApplicationSet適用
kubectl apply -f argocd/multi-cloud-appset.yaml
```

## 成功基準

- [ ] 3つのクラウドでのKubernetes稼働
- [ ] クロスクラウドネットワーク接続（<100ms）
- [ ] グローバルロードバランシングの動作
- [ ] データの地理的レプリケーション
- [ ] 統一CI/CDパイプライン

## 運用ガイド

### コスト監視
```bash
# 月次コストレポート
./scripts/generate-cost-report.sh

# 最適化提案
./scripts/cost-optimization-recommendations.sh
```

### 障害対応
```bash
# クラウド障害シミュレーション
./scripts/simulate-cloud-failure.sh --cloud aws

# フェイルオーバー確認
./scripts/verify-failover.sh
```

## トラブルシューティング

### 問題: ネットワーク接続性
```bash
# VPN状態確認
terraform show -json | jq '.values.root_module.child_modules[].resources[] | select(.type == "aws_vpn_connection")'

# 接続テスト
./scripts/test-cross-cloud-connectivity.sh
```

### 問題: データ同期遅延
```bash
# レプリケーションラグ確認
cockroach sql --execute "SHOW RANGES FROM DATABASE mydb"

# ネットワーク遅延測定
./scripts/measure-inter-cloud-latency.sh
```

## 次のステップ

マルチクラウド展開を確立後、`18_edge_computing_iot`でエッジコンピューティングとIoT統合を実装します。

## 学んだこと

- クラウド抽象化の重要性
- ベンダーロックイン回避戦略
- グローバル分散システムの複雑性
- コスト最適化の継続的必要性

## 参考資料

- [Multi-Cloud Strategy Guide](https://cloud.google.com/solutions/multi-cloud-strategy)
- [HashiCorp Multi-Cloud](https://www.hashicorp.com/solutions/multi-cloud-infrastructure)
- [CNCF Multi-Cloud](https://www.cncf.io/blog/2021/11/10/multi-cloud-is-the-future/)
- [Terraform Multi-Cloud Patterns](https://learn.hashicorp.com/collections/terraform/aws)