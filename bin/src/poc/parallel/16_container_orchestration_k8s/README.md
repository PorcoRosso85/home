# 16_container_orchestration_k8s

## 概要

Kubernetesを使用した本格的なコンテナオーケストレーションを実装し、自動スケーリング、自己修復、ローリングアップデート、サービスメッシュ統合を実現します。

## 目的

- Kubernetesクラスターの構築と管理
- 宣言的デプロイメントと自動化
- 水平自動スケーリング（HPA/VPA）
- 高度なネットワーキングとサービス発見

## アーキテクチャ

```
┌─────────────────────────────────────┐
│       Kubernetes Control Plane      │
│  ┌─────────┬──────────┬─────────┐  │
│  │ API     │Scheduler │Controller│  │
│  │ Server  │          │ Manager  │  │
│  └─────────┴──────────┴─────────┘  │
│         etcd cluster (3 nodes)      │
└─────────────────┬───────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┐
    │             │             │             │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│Worker-1│    │Worker-2│    │Worker-3│    │Worker-4│
│        │    │        │    │        │    │        │
│┌─────┐ │    │┌─────┐ │    │┌─────┐ │    │┌─────┐ │
││Pod A│ │    ││Pod B│ │    ││Pod C│ │    ││Pod D│ │
││     │ │    ││     │ │    ││     │ │    ││     │ │
│└─────┘ │    │└─────┘ │    │└─────┘ │    │└─────┘ │
│┌─────┐ │    │┌─────┐ │    │┌─────┐ │    │┌─────┐ │
││Pod E│ │    ││Pod F│ │    ││Pod G│ │    ││Pod H│ │
│└─────┘ │    │└─────┘ │    │└─────┘ │    │└─────┘ │
│ kubelet│    │ kubelet│    │ kubelet│    │ kubelet│
│ kube-  │    │ kube-  │    │ kube-  │    │ kube-  │
│ proxy  │    │ proxy  │    │ proxy  │    │ proxy  │
└────────┘    └────────┘    └────────┘    └────────┘
     │             │             │             │
     └─────────────┼─────────────┼─────────────┘
                   │             │
              [Overlay Network (CNI)]
```

## 検証項目

### 1. クラスター管理
- **マルチノードクラスター**: コントロールプレーンのHA
- **ノード管理**: 追加、削除、ドレイン
- **RBAC**: 役割ベースのアクセス制御
- **ネームスペース**: マルチテナンシー

### 2. ワークロード管理
- **Deployment**: 宣言的アプリケーション管理
- **StatefulSet**: ステートフルアプリケーション
- **DaemonSet**: ノードごとのデーモン
- **Job/CronJob**: バッチ処理

### 3. 自動スケーリング
- **HPA**: CPU/メモリベースの水平スケーリング
- **VPA**: 垂直スケーリング
- **Cluster Autoscaler**: ノード自動スケーリング
- **Custom Metrics**: カスタムメトリクスベース

### 4. 高度な機能
- **Service Mesh**: Istio統合
- **Ingress**: L7ロードバランシング
- **NetworkPolicy**: マイクロセグメンテーション
- **PodDisruptionBudget**: 可用性保証

## TDDアプローチ

### Red Phase (Kubernetesオーケストレーションのテスト)
```typescript
// test/k8s-orchestration.test.ts
import { assertEquals, assert, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { describe, it, beforeAll } from "https://deno.land/std@0.208.0/testing/bdd.ts";
import { delay } from "https://deno.land/std@0.208.0/async/delay.ts";

describe('Kubernetes Orchestration', () => {
  let kc: any;
  let k8sApi: any;
  let appsApi: any;
  let autoscalingApi: any;
  
  beforeAll(async () => {
    // Kubernetes クライアントの初期化
    // Note: In Deno, we'll use the Kubernetes API directly via fetch
    const kubeConfig = await Deno.readTextFile(`${Deno.env.get('HOME')}/.kube/config`);
    const config = JSON.parse(kubeConfig);
    
    // Initialize API clients
    k8sApi = new K8sApiClient(config, 'v1');
    appsApi = new K8sApiClient(config, 'apps/v1');
    autoscalingApi = new K8sApiClient(config, 'autoscaling/v2');
  });

  it('should deploy application with rolling update', async () => {
    const deployment = {
      apiVersion: 'apps/v1',
      kind: 'Deployment',
      metadata: {
        name: 'web-app',
        namespace: 'default'
      },
      spec: {
        replicas: 3,
        selector: {
          matchLabels: { app: 'web' }
        },
        template: {
          metadata: {
            labels: { app: 'web' }
          },
          spec: {
            containers: [{
              name: 'web',
              image: 'webapp:v1.0',
              ports: [{ containerPort: 8080 }],
              resources: {
                requests: {
                  cpu: '100m',
                  memory: '128Mi'
                },
                limits: {
                  cpu: '500m',
                  memory: '512Mi'
                }
              },
              livenessProbe: {
                httpGet: {
                  path: '/health',
                  port: 8080
                },
                initialDelaySeconds: 30,
                periodSeconds: 10
              },
              readinessProbe: {
                httpGet: {
                  path: '/ready',
                  port: 8080
                },
                initialDelaySeconds: 5,
                periodSeconds: 5
              }
            }]
          }
        },
        strategy: {
          type: 'RollingUpdate',
          rollingUpdate: {
            maxSurge: 1,
            maxUnavailable: 0
          }
        }
      }
    };
    
    // デプロイメント作成
    await appsApi.createNamespacedDeployment('default', deployment);
    
    // デプロイメント完了を待つ
    await waitForDeployment('default', 'web-app', 180000); // 3分
    
    // すべてのPodが起動していることを確認
    const pods = await k8sApi.listNamespacedPod(
      'default',
      undefined,
      undefined,
      undefined,
      undefined,
      'app=web'
    );
    
    assertEquals(pods.body.items.length, 3);
    
    // すべてのPodがRunning状態
    pods.body.items.forEach(pod => {
      assertEquals(pod.status.phase, 'Running');
      assertEquals(pod.status.conditions.find((c: any) => c.type === 'Ready').status, 'True');
    });
    
    // ローリングアップデートのテスト
    const updatedDeployment = await appsApi.readNamespacedDeployment('web-app', 'default');
    updatedDeployment.body.spec.template.spec.containers[0].image = 'webapp:v2.0';
    
    await appsApi.replaceNamespacedDeployment(
      'web-app',
      'default',
      updatedDeployment.body
    );
    
    // アップデート中の可用性確認
    const availabilityCheck = setInterval(async () => {
      const currentPods = await k8sApi.listNamespacedPod(
        'default',
        undefined,
        undefined,
        undefined,
        undefined,
        'app=web'
      );
      
      const readyPods = currentPods.body.items.filter(pod => 
        pod.status.conditions?.find(c => c.type === 'Ready')?.status === 'True'
      );
      
      // 最低2つのPodが常に利用可能
      assert(readyPods.length >= 2);
    }, 5000);
    
    // アップデート完了を待つ
    await waitForDeployment('default', 'web-app', 180000);
    
    clearInterval(availabilityCheck);
    
    // 新バージョンの確認
    const updatedPods = await k8sApi.listNamespacedPod(
      'default',
      undefined,
      undefined,
      undefined,
      undefined,
      'app=web'
    );
    
    updatedPods.body.items.forEach(pod => {
      const containerImage = pod.spec.containers[0].image;
      assertEquals(containerImage, 'webapp:v2.0');
    });
  });

  it('should auto-scale based on CPU usage', async () => {
    // HPA (Horizontal Pod Autoscaler) の作成
    const hpa = {
      apiVersion: 'autoscaling/v2',
      kind: 'HorizontalPodAutoscaler',
      metadata: {
        name: 'web-app-hpa'
      },
      spec: {
        scaleTargetRef: {
          apiVersion: 'apps/v1',
          kind: 'Deployment',
          name: 'web-app'
        },
        minReplicas: 2,
        maxReplicas: 10,
        metrics: [{
          type: 'Resource',
          resource: {
            name: 'cpu',
            target: {
              type: 'Utilization',
              averageUtilization: 50
            }
          }
        }, {
          type: 'Resource',
          resource: {
            name: 'memory',
            target: {
              type: 'Utilization',
              averageUtilization: 70
            }
          }
        }],
        behavior: {
          scaleDown: {
            stabilizationWindowSeconds: 300,
            policies: [{
              type: 'Percent',
              value: 10,
              periodSeconds: 60
            }]
          },
          scaleUp: {
            stabilizationWindowSeconds: 60,
            policies: [{
              type: 'Percent',
              value: 100,
              periodSeconds: 60
            }, {
              type: 'Pods',
              value: 4,
              periodSeconds: 60
            }]
          }
        }
      }
    };
    
    await autoscalingApi.createNamespacedHorizontalPodAutoscaler('default', hpa);
    
    // 負荷生成Job
    const loadJob = {
      apiVersion: 'batch/v1',
      kind: 'Job',
      metadata: {
        name: 'load-generator'
      },
      spec: {
        template: {
          spec: {
            containers: [{
              name: 'load',
              image: 'busybox',
              command: [
                'sh',
                '-c',
                'while true; do wget -q -O- http://web-app-service:8080/cpu-intensive; done'
              ]
            }],
            restartPolicy: 'Never'
          }
        },
        parallelism: 5,
        completions: 5
      }
    };
    
    await k8sApi.createNamespacedJob('default', loadJob);
    
    // スケーリングを監視
    const scalingEvents = [];
    const startTime = Date.now();
    
    const monitorInterval = setInterval(async () => {
      const currentHPA = await autoscalingApi.readNamespacedHorizontalPodAutoscaler(
        'web-app-hpa',
        'default'
      );
      
      const currentReplicas = currentHPA.body.status.currentReplicas;
      const targetReplicas = currentHPA.body.status.desiredReplicas;
      const currentCPU = currentHPA.body.status.currentMetrics?.find(m => m.resource?.name === 'cpu');
      
      scalingEvents.push({
        timestamp: Date.now() - startTime,
        currentReplicas,
        targetReplicas,
        cpuUtilization: currentCPU?.resource?.current?.averageUtilization
      });
      
      console.log(`Replicas: ${currentReplicas}/${targetReplicas}, CPU: ${currentCPU?.resource?.current?.averageUtilization}%`);
    }, 10000);
    
    // 5分間監視
    await delay(300000);
    
    clearInterval(monitorInterval);
    
    // 負荷停止
    await k8sApi.deleteNamespacedJob('load-generator', 'default');
    
    // スケーリングが発生したことを確認
    const maxReplicas = Math.max(...scalingEvents.map(e => e.currentReplicas));
    assert(maxReplicas > 3); // 初期値3から増加
    
    // CPU使用率が閾値を超えた時にスケールアップ
    const highCPUEvents = scalingEvents.filter(e => e.cpuUtilization > 50);
    assert(highCPUEvents.length > 0);
  });

  it('should handle pod disruptions gracefully', async () => {
    // PodDisruptionBudget の作成
    const pdb = {
      apiVersion: 'policy/v1',
      kind: 'PodDisruptionBudget',
      metadata: {
        name: 'web-app-pdb'
      },
      spec: {
        minAvailable: 2,
        selector: {
          matchLabels: {
            app: 'web'
          }
        }
      }
    };
    
    await k8sApi.createNamespacedPodDisruptionBudget('default', pdb);
    
    // ノードのドレインをシミュレート
    const nodes = await k8sApi.listNode();
    const targetNode = nodes.body.items[0];
    
    // ノードをcordon（新規Pod配置を防止）
    await k8sApi.patchNode(targetNode.metadata.name, {
      spec: { unschedulable: true }
    }, undefined, undefined, undefined, undefined, {
      headers: { 'Content-Type': 'application/merge-patch+json' }
    });
    
    // ノード上のPodを取得
    const podsOnNode = await k8sApi.listPodForAllNamespaces(
      undefined,
      undefined,
      `spec.nodeName=${targetNode.metadata.name}`
    );
    
    const webPods = podsOnNode.body.items.filter(pod => 
      pod.metadata.labels?.app === 'web'
    );
    
    // Podの退避を試みる
    const evictionResults = [];
    
    for (const pod of webPods) {
      try {
        await k8sApi.createNamespacedPodEviction(
          pod.metadata.name,
          pod.metadata.namespace,
          {
            apiVersion: 'policy/v1',
            kind: 'Eviction',
            metadata: {
              name: pod.metadata.name,
              namespace: pod.metadata.namespace
            }
          }
        );
        evictionResults.push({ pod: pod.metadata.name, success: true });
      } catch (error) {
        evictionResults.push({ 
          pod: pod.metadata.name, 
          success: false, 
          reason: error.response?.body?.message 
        });
      }
    }
    
    // PDBにより一部の退避が拒否されることを確認
    const blockedEvictions = evictionResults.filter(r => !r.success);
    assert(blockedEvictions.length > 0);
    assert(blockedEvictions[0].reason.includes('PodDisruptionBudget'));
    
    // サービスが引き続き利用可能
    const remainingPods = await k8sApi.listNamespacedPod(
      'default',
      undefined,
      undefined,
      undefined,
      undefined,
      'app=web'
    );
    
    const readyPods = remainingPods.body.items.filter(pod =>
      pod.status.conditions?.find(c => c.type === 'Ready')?.status === 'True'
    );
    
    assert(readyPods.length >= 2); // minAvailable
  });

  it('should implement service mesh with Istio', async () => {
    // Istio サイドカー injection
    const deploymentWithIstio = {
      apiVersion: 'apps/v1',
      kind: 'Deployment',
      metadata: {
        name: 'web-app-istio',
        namespace: 'default',
        labels: {
          version: 'v1'
        }
      },
      spec: {
        replicas: 2,
        selector: {
          matchLabels: { app: 'web-istio' }
        },
        template: {
          metadata: {
            labels: { 
              app: 'web-istio',
              version: 'v1'
            },
            annotations: {
              'sidecar.istio.io/inject': 'true'
            }
          },
          spec: {
            containers: [{
              name: 'web',
              image: 'webapp:v1.0',
              ports: [{ containerPort: 8080 }]
            }]
          }
        }
      }
    };
    
    await appsApi.createNamespacedDeployment('default', deploymentWithIstio);
    
    // VirtualService の作成
    const virtualService = {
      apiVersion: 'networking.istio.io/v1beta1',
      kind: 'VirtualService',
      metadata: {
        name: 'web-app-vs'
      },
      spec: {
        hosts: ['web-app-istio'],
        http: [{
          match: [{
            headers: {
              'x-version': {
                exact: 'v2'
              }
            }
          }],
          route: [{
            destination: {
              host: 'web-app-istio',
              subset: 'v2'
            }
          }]
        }, {
          route: [{
            destination: {
              host: 'web-app-istio',
              subset: 'v1'
            },
            weight: 90
          }, {
            destination: {
              host: 'web-app-istio',
              subset: 'v2'
            },
            weight: 10
          }]
        }]
      }
    };
    
    // カスタムリソースの作成
    const customObjectsApi = kc.makeApiClient(k8s.CustomObjectsApi);
    
    await customObjectsApi.createNamespacedCustomObject(
      'networking.istio.io',
      'v1beta1',
      'default',
      'virtualservices',
      virtualService
    );
    
    // DestinationRule の作成
    const destinationRule = {
      apiVersion: 'networking.istio.io/v1beta1',
      kind: 'DestinationRule',
      metadata: {
        name: 'web-app-dr'
      },
      spec: {
        host: 'web-app-istio',
        trafficPolicy: {
          connectionPool: {
            tcp: {
              maxConnections: 100
            },
            http: {
              http1MaxPendingRequests: 10,
              http2MaxRequests: 100
            }
          },
          outlierDetection: {
            consecutiveErrors: 5,
            interval: '30s',
            baseEjectionTime: '30s'
          }
        },
        subsets: [{
          name: 'v1',
          labels: { version: 'v1' }
        }, {
          name: 'v2',
          labels: { version: 'v2' }
        }]
      }
    };
    
    await customObjectsApi.createNamespacedCustomObject(
      'networking.istio.io',
      'v1beta1',
      'default',
      'destinationrules',
      destinationRule
    );
    
    // サイドカーが注入されたことを確認
    await waitForDeployment('default', 'web-app-istio', 120000);
    
    const istioizedPods = await k8sApi.listNamespacedPod(
      'default',
      undefined,
      undefined,
      undefined,
      undefined,
      'app=web-istio'
    );
    
    istioizedPods.body.items.forEach(pod => {
      // Envoyサイドカーコンテナの存在確認
      const containers = pod.spec.containers.map(c => c.name);
      assert(containers.includes('istio-proxy'));
      
      // 2つのコンテナ（アプリ + サイドカー）
      assertEquals(containers.length, 2);
    });
  });

  it('should manage stateful applications', async () => {
    // StatefulSet for database cluster
    const statefulSet = {
      apiVersion: 'apps/v1',
      kind: 'StatefulSet',
      metadata: {
        name: 'postgres-cluster'
      },
      spec: {
        serviceName: 'postgres-headless',
        replicas: 3,
        selector: {
          matchLabels: { app: 'postgres' }
        },
        template: {
          metadata: {
            labels: { app: 'postgres' }
          },
          spec: {
            containers: [{
              name: 'postgres',
              image: 'postgres:15',
              ports: [{ containerPort: 5432 }],
              env: [
                { name: 'POSTGRES_DB', value: 'testdb' },
                { name: 'POSTGRES_USER', value: 'postgres' },
                { name: 'POSTGRES_PASSWORD', value: 'postgres' },
                { name: 'PGDATA', value: '/var/lib/postgresql/data/pgdata' }
              ],
              volumeMounts: [{
                name: 'postgres-storage',
                mountPath: '/var/lib/postgresql/data'
              }],
              livenessProbe: {
                exec: {
                  command: ['pg_isready', '-U', 'postgres']
                },
                initialDelaySeconds: 30,
                periodSeconds: 10
              }
            }]
          }
        },
        volumeClaimTemplates: [{
          metadata: {
            name: 'postgres-storage'
          },
          spec: {
            accessModes: ['ReadWriteOnce'],
            resources: {
              requests: {
                storage: '10Gi'
              }
            }
          }
        }],
        updateStrategy: {
          type: 'RollingUpdate'
        },
        podManagementPolicy: 'OrderedReady'
      }
    };
    
    // Headless Service
    const headlessService = {
      apiVersion: 'v1',
      kind: 'Service',
      metadata: {
        name: 'postgres-headless'
      },
      spec: {
        clusterIP: 'None',
        selector: {
          app: 'postgres'
        },
        ports: [{
          port: 5432,
          targetPort: 5432
        }]
      }
    };
    
    await k8sApi.createNamespacedService('default', headlessService);
    await appsApi.createNamespacedStatefulSet('default', statefulSet);
    
    // StatefulSetの起動を待つ
    await waitForStatefulSet('default', 'postgres-cluster', 300000);
    
    // 順序付き起動の確認
    const pods = await k8sApi.listNamespacedPod(
      'default',
      undefined,
      undefined,
      undefined,
      undefined,
      'app=postgres'
    );
    
    // Pod名の順序確認
    const podNames = pods.body.items.map(p => p.metadata.name).sort();
    assertEquals(podNames, [
      'postgres-cluster-0',
      'postgres-cluster-1',
      'postgres-cluster-2'
    ]);
    
    // 各Podが個別のPVCを持つことを確認
    for (let i = 0; i < 3; i++) {
      const pvcName = `postgres-storage-postgres-cluster-${i}`;
      const pvc = await k8sApi.readNamespacedPersistentVolumeClaim(pvcName, 'default');
      
      assertEquals(pvc.body.status.phase, 'Bound');
      assertEquals(pvc.body.spec.resources.requests.storage, '10Gi');
    }
    
    // 安定したネットワークIDの確認
    const dnsTests = [
      'postgres-cluster-0.postgres-headless.default.svc.cluster.local',
      'postgres-cluster-1.postgres-headless.default.svc.cluster.local',
      'postgres-cluster-2.postgres-headless.default.svc.cluster.local'
    ];
    
    for (const hostname of dnsTests) {
      const testPod = {
        apiVersion: 'v1',
        kind: 'Pod',
        metadata: {
          name: `dns-test-${Date.now()}`,
          namespace: 'default'
        },
        spec: {
          containers: [{
            name: 'test',
            image: 'busybox',
            command: ['nslookup', hostname]
          }],
          restartPolicy: 'Never'
        }
      };
      
      const created = await k8sApi.createNamespacedPod('default', testPod);
      await waitForPodCompletion('default', created.body.metadata.name);
      
      const logs = await k8sApi.readNamespacedPodLog(
        created.body.metadata.name,
        'default'
      );
      
      assert(logs.body.includes('Address'));
      
      // クリーンアップ
      await k8sApi.deleteNamespacedPod(created.body.metadata.name, 'default');
    }
  });

  it('should implement network policies', async () => {
    // ネットワークポリシーの作成
    const networkPolicy = {
      apiVersion: 'networking.k8s.io/v1',
      kind: 'NetworkPolicy',
      metadata: {
        name: 'web-netpol'
      },
      spec: {
        podSelector: {
          matchLabels: {
            app: 'web'
          }
        },
        policyTypes: ['Ingress', 'Egress'],
        ingress: [{
          from: [
            {
              podSelector: {
                matchLabels: {
                  app: 'frontend'
                }
              }
            },
            {
              namespaceSelector: {
                matchLabels: {
                  name: 'monitoring'
                }
              }
            }
          ],
          ports: [{
            protocol: 'TCP',
            port: 8080
          }]
        }],
        egress: [{
          to: [{
            podSelector: {
              matchLabels: {
                app: 'database'
              }
            }
          }],
          ports: [{
            protocol: 'TCP',
            port: 5432
          }]
        }, {
          to: [{
            namespaceSelector: {}
          }],
          ports: [{
            protocol: 'TCP',
            port: 53
          }, {
            protocol: 'UDP',
            port: 53
          }]
        }]
      }
    };
    
    await k8sApi.createNamespacedNetworkPolicy('default', networkPolicy);
    
    // テスト用のPod作成
    const testPods = [
      { name: 'allowed-client', labels: { app: 'frontend' } },
      { name: 'denied-client', labels: { app: 'hacker' } }
    ];
    
    for (const podSpec of testPods) {
      await k8sApi.createNamespacedPod('default', {
        apiVersion: 'v1',
        kind: 'Pod',
        metadata: {
          name: podSpec.name,
          labels: podSpec.labels
        },
        spec: {
          containers: [{
            name: 'test',
            image: 'nicolaka/netshoot',
            command: ['sleep', '3600']
          }]
        }
      });
    }
    
    // Podの起動を待つ
    await Promise.all(
      testPods.map(p => waitForPodReady('default', p.name))
    );
    
    // 接続テスト
    const webPod = (await k8sApi.listNamespacedPod(
      'default',
      undefined,
      undefined,
      undefined,
      undefined,
      'app=web'
    )).body.items[0];
    
    const webIP = webPod.status.podIP;
    
    // 許可されたクライアントからの接続
    const allowedExec = await k8sApi.exec(
      'default',
      'allowed-client',
      'test',
      ['nc', '-zv', webIP, '8080'],
      process.stdout,
      process.stderr,
      process.stdin,
      false
    );
    
    assert(allowedExec.includes('succeeded'));
    
    // 拒否されたクライアントからの接続
    const deniedExec = await k8sApi.exec(
      'default',
      'denied-client',
      'test',
      ['timeout', '5', 'nc', '-zv', webIP, '8080'],
      process.stdout,
      process.stderr,
      process.stdin,
      false
    );
    
    assert(deniedExec.includes('timeout'));
  });
});

// ヘルパー関数
async function waitForDeployment(namespace: string, name: string, timeout: number) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    const deployment = await appsApi.readNamespacedDeployment(name, namespace);
    const status = deployment.body.status;
    
    if (status.replicas === status.readyReplicas &&
        status.replicas === status.updatedReplicas) {
      return;
    }
    
    await delay(5000);
  }
  
  throw new Error(`Deployment ${name} did not become ready in time`);
}

async function waitForStatefulSet(namespace: string, name: string, timeout: number) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    const sts = await appsApi.readNamespacedStatefulSet(name, namespace);
    const status = sts.body.status;
    
    if (status.replicas === status.readyReplicas &&
        status.replicas === status.currentReplicas) {
      return;
    }
    
    await delay(5000);
  }
  
  throw new Error(`StatefulSet ${name} did not become ready in time`);
}
```

### Green Phase (Kubernetes実装)
```yaml
# k8s-manifests/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: parallel-poc
  labels:
    istio-injection: enabled
```

```yaml
# k8s-manifests/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
  namespace: parallel-poc
  labels:
    app: web
    version: v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
        version: v1
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - web
              topologyKey: kubernetes.io/hostname
      containers:
      - name: web
        image: webapp:v1.0
        ports:
        - containerPort: 8080
          name: http
        - containerPort: 9090
          name: metrics
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          successThreshold: 1
          failureThreshold: 3
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: secrets
          mountPath: /app/secrets
          readOnly: true
      volumes:
      - name: config
        configMap:
          name: web-app-config
      - name: secrets
        secret:
          secretName: web-app-secrets
```

```yaml
# k8s-manifests/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: web-app-service
  namespace: parallel-poc
  labels:
    app: web
spec:
  type: ClusterIP
  selector:
    app: web
  ports:
  - name: http
    port: 80
    targetPort: 8080
    protocol: TCP
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
---
apiVersion: v1
kind: Service
metadata:
  name: web-app-headless
  namespace: parallel-poc
spec:
  clusterIP: None
  selector:
    app: web
  ports:
  - port: 8080
    targetPort: 8080
```

```yaml
# k8s-manifests/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: web-app-hpa
  namespace: parallel-poc
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
      - type: Pods
        value: 1
        periodSeconds: 120
      selectPolicy: Min
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Max
```

```yaml
# k8s-manifests/pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: web-app-pdb
  namespace: parallel-poc
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: web
  maxUnavailable: 33%
```

```yaml
# k8s-manifests/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-app-ingress
  namespace: parallel-poc
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - webapp.example.com
    secretName: webapp-tls
  rules:
  - host: webapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web-app-service
            port:
              number: 80
```

```yaml
# k8s-manifests/networkpolicy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: web-app-network-policy
  namespace: parallel-poc
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

```typescript
// app/k8s-aware-app.ts
import { delay } from "https://deno.land/std@0.208.0/async/delay.ts";

class K8sAwareApplication {
  private metrics: any;
  private server: Deno.HttpServer | null = null;
  private activeConnections = 0;
  private requestCount = 0;
  
  constructor() {
    this.metrics = this.setupMetrics();
    this.setupK8sIntegration();
  }
  
  setupMetrics() {
    // 簡易的なメトリクス実装
    const metrics = {
      httpRequestDurations: new Map<string, number[]>(),
      httpRequestCounts: new Map<string, number>(),
      httpRequestsPerSecond: 0,
      startTime: Date.now()
    };
    
    return {
      recordRequest: (method: string, path: string, status: number, duration: number) => {
        const key = `${method}_${path}_${status}`;
        
        // Duration tracking
        if (!metrics.httpRequestDurations.has(key)) {
          metrics.httpRequestDurations.set(key, []);
        }
        metrics.httpRequestDurations.get(key)!.push(duration);
        
        // Count tracking
        const currentCount = metrics.httpRequestCounts.get(key) || 0;
        metrics.httpRequestCounts.set(key, currentCount + 1);
      },
      
      getMetrics: () => {
        const lines: string[] = [
          '# HELP http_request_duration_seconds Duration of HTTP requests in seconds',
          '# TYPE http_request_duration_seconds histogram'
        ];
        
        // Convert metrics to Prometheus format
        metrics.httpRequestDurations.forEach((durations, key) => {
          const [method, path, status] = key.split('_');
          const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
          lines.push(`http_request_duration_seconds{method="${method}",route="${path}",status="${status}"} ${avg}`);
        });
        
        lines.push('', '# HELP http_requests_total Total number of HTTP requests');
        lines.push('# TYPE http_requests_total counter');
        
        metrics.httpRequestCounts.forEach((count, key) => {
          const [method, path, status] = key.split('_');
          lines.push(`http_requests_total{method="${method}",route="${path}",status="${status}"} ${count}`);
        });
        
        lines.push('', '# HELP http_requests_per_second HTTP requests per second');
        lines.push('# TYPE http_requests_per_second gauge');
        lines.push(`http_requests_per_second ${metrics.httpRequestsPerSecond}`);
        
        return lines.join('\n');
      },
      
      updateRequestsPerSecond: (rps: number) => {
        metrics.httpRequestsPerSecond = rps;
      }
    };
  }
  
  async handleRequest(request: Request): Promise<Response> {
    const start = Date.now();
    const url = new URL(request.url);
    const method = request.method;
    const path = url.pathname;
    let status = 200;
    
    this.activeConnections++;
    this.requestCount++;
    
    try {
      // ヘルスチェック
      if (path === '/health' && method === 'GET') {
        const health = this.checkHealth();
        
        if (health.status === 'healthy') {
          return new Response(JSON.stringify(health), {
            headers: { 'content-type': 'application/json' }
          });
        } else {
          status = 503;
          return new Response(JSON.stringify(health), {
            status: 503,
            headers: { 'content-type': 'application/json' }
          });
        }
      }
      
      // レディネスチェック
      if (path === '/ready' && method === 'GET') {
        const readiness = this.checkReadiness();
        
        if (readiness.ready) {
          return new Response(JSON.stringify(readiness), {
            headers: { 'content-type': 'application/json' }
          });
        } else {
          status = 503;
          return new Response(JSON.stringify(readiness), {
            status: 503,
            headers: { 'content-type': 'application/json' }
          });
        }
      }
      
      // メトリクスエンドポイント
      if (path === '/metrics' && method === 'GET') {
        return new Response(this.metrics.getMetrics(), {
          headers: { 'content-type': 'text/plain; version=0.0.4' }
        });
      }
      
      // アプリケーションルート
      if (path === '/' && method === 'GET') {
        return new Response(JSON.stringify({
          message: 'Hello from Kubernetes!',
          pod: Deno.env.get('POD_NAME'),
          namespace: Deno.env.get('POD_NAMESPACE'),
          node: Deno.env.get('NODE_NAME'),
          version: Deno.env.get('APP_VERSION') || 'v1.0'
        }), {
          headers: { 'content-type': 'application/json' }
        });
      }
      
      // CPU負荷エンドポイント（オートスケーリングテスト用）
      if (path === '/cpu-intensive' && method === 'GET') {
        const cpuStart = Date.now();
        const duration = parseInt(url.searchParams.get('duration') || '1000');
        
        // CPU集約的な処理
        while (Date.now() - cpuStart < duration) {
          Math.sqrt(Math.random());
        }
        
        return new Response(JSON.stringify({
          duration: Date.now() - cpuStart,
          pod: Deno.env.get('POD_NAME')
        }), {
          headers: { 'content-type': 'application/json' }
        });
      }
      
      // 404 Not Found
      status = 404;
      return new Response('Not Found', { status: 404 });
      
    } finally {
      const duration = (Date.now() - start) / 1000;
      this.metrics.recordRequest(method, path, status, duration);
      this.activeConnections--;
    }
  }
  
  setupK8sIntegration() {
    // Graceful shutdown
    Deno.addSignalListener('SIGTERM', async () => {
      console.log('SIGTERM received, starting graceful shutdown');
      
      // 既存の接続が完了するのを待つ
      await this.drainConnections();
      
      // クリーンアップ
      await this.cleanup();
      
      Deno.exit(0);
    });
    
    // リーダー選出（StatefulSetの場合）
    if (Deno.env.get('ENABLE_LEADER_ELECTION') === 'true') {
      this.setupLeaderElection();
    }
  }
  
  checkHealth() {
    // 基本的なヘルスチェック
    const checks = {
      memory: this.checkMemory(),
      disk: this.checkDisk(),
      dependencies: this.checkDependencies()
    };
    
    const allHealthy = Object.values(checks).every(c => c.healthy);
    
    return {
      status: allHealthy ? 'healthy' : 'unhealthy',
      checks,
      timestamp: new Date().toISOString()
    };
  }
  
  checkReadiness() {
    // アプリケーションの準備状態
    const checks = {
      database: this.isDatabaseReady(),
      cache: this.isCacheReady(),
      initialized: this.isInitialized()
    };
    
    const allReady = Object.values(checks).every(c => c);
    
    return {
      ready: allReady,
      checks,
      timestamp: new Date().toISOString()
    };
  }
  
  checkMemory() {
    // Note: Deno.systemMemoryInfo() is not available in all environments
    // This is a simplified implementation
    const limit = parseInt(Deno.env.get('MEMORY_LIMIT') || '536870912'); // 512MB default
    const usage = 0.5; // Mock value for demonstration
    
    return {
      healthy: usage < 0.9,
      usage: usage,
      used: usage * limit,
      limit: limit
    };
  }
  
  async drainConnections() {
    // アクティブな接続の追跡と完了待機
    const timeout = 30000; // 30秒
    const start = Date.now();
    
    while (this.activeConnections > 0 && Date.now() - start < timeout) {
      console.log(`Waiting for ${this.activeConnections} connections to complete`);
      await delay(1000);
    }
  }
  
  async start() {
    const port = parseInt(Deno.env.get('PORT') || '8080');
    
    console.log(`K8s-aware app listening on port ${port}`);
    console.log(`Pod: ${Deno.env.get('POD_NAME')}`);
    console.log(`Namespace: ${Deno.env.get('POD_NAMESPACE')}`);
    
    // RPS計算
    let lastRequestCount = 0;
    setInterval(() => {
      const rps = this.requestCount - lastRequestCount;
      this.metrics.updateRequestsPerSecond(rps);
      lastRequestCount = this.requestCount;
    }, 1000);
    
    // サーバー起動
    this.server = Deno.serve(
      { port },
      (request) => this.handleRequest(request)
    );
    
    await this.server.finished;
  }
  
  private setupLeaderElection() {
    // Leader election logic for StatefulSets
    console.log('Leader election enabled');
  }
  
  private async cleanup() {
    console.log('Performing cleanup...');
  }
  
  private checkDisk() {
    return { healthy: true, usage: 0.5 };
  }
  
  private checkDependencies() {
    return { healthy: true };
  }
  
  private isDatabaseReady() {
    return true;
  }
  
  private isCacheReady() {
    return true;
  }
  
  private isInitialized() {
    return true;
  }
}

// 起動
if (import.meta.main) {
  const app = new K8sAwareApplication();
  await app.start();
}

export { K8sAwareApplication };
```

### Kubernetes設定スクリプト
```bash
#!/bin/bash
# setup-k8s-cluster.sh

# Kind（Kubernetes in Docker）を使用したローカルクラスター
cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: parallel-poc
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
- role: worker
networking:
  disableDefaultCNI: false
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
EOF

# Ingress Nginxのインストール
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# Metrics Serverのインストール
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Istioのインストール（オプション）
if [ "$ENABLE_ISTIO" = "true" ]; then
  curl -L https://istio.io/downloadIstio | sh -
  cd istio-*
  ./bin/istioctl install --set profile=demo -y
  kubectl label namespace default istio-injection=enabled
  cd ..
fi

# アプリケーションのデプロイ
kubectl create namespace parallel-poc
kubectl apply -f k8s-manifests/

# 起動確認
kubectl wait --for=condition=ready pod -l app=web -n parallel-poc --timeout=300s

echo "Kubernetes cluster is ready!"
echo "Access the application at: http://localhost"
```

## 実行と検証

### 1. クラスターセットアップ
```bash
# クラスターの作成
./setup-k8s-cluster.sh

# 状態確認
kubectl get nodes
kubectl get pods -n parallel-poc
```

### 2. アプリケーションのデプロイ
```bash
# デプロイ
kubectl apply -k k8s-manifests/

# ログ確認
kubectl logs -f deployment/web-app -n parallel-poc
```

### 3. オートスケーリングテスト
```bash
# 負荷生成
kubectl run load-generator \
  --image=busybox \
  --restart=Never \
  -- /bin/sh -c "while true; do wget -q -O- http://web-app-service.parallel-poc/cpu-intensive; done"

# HPA監視
kubectl get hpa -n parallel-poc -w
```

## 成功基準

- [ ] 3ノード以上のクラスター構築
- [ ] ローリングアップデートでゼロダウンタイム
- [ ] CPU使用率50%での自動スケーリング
- [ ] PodDisruptionBudgetによる可用性保証
- [ ] NetworkPolicyによるセキュリティ隔離

## 運用ガイド

### アプリケーション更新
```bash
# イメージの更新
kubectl set image deployment/web-app web=webapp:v2.0 -n parallel-poc

# ロールアウト状態確認
kubectl rollout status deployment/web-app -n parallel-poc

# ロールバック（必要な場合）
kubectl rollout undo deployment/web-app -n parallel-poc
```

### トラブルシューティング
```bash
# Pod の詳細情報
kubectl describe pod <pod-name> -n parallel-poc

# イベント確認
kubectl get events -n parallel-poc --sort-by='.lastTimestamp'

# リソース使用状況
kubectl top nodes
kubectl top pods -n parallel-poc
```

## 次のステップ

Kubernetesオーケストレーションを確立後、`17_multi_cloud_deployment`でマルチクラウド展開を実装します。

## 学んだこと

- 宣言的インフラストラクチャの威力
- 自動化されたオペレーションの利点
- コンテナオーケストレーションの複雑性
- クラウドネイティブアプリケーション設計

## 参考資料

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kubernetes Patterns](https://www.oreilly.com/library/view/kubernetes-patterns/9781492050278/)
- [Production-Grade Container Orchestration](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/)
- [CNCF Cloud Native Interactive Landscape](https://landscape.cncf.io/)