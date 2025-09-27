# What is Consul?

HashiCorp Consul is a service networking solution that enables teams to manage secure network connectivity between services and across on-prem and multi-cloud environments and runtimes. Consul offers service discovery, service mesh, traffic management, and automated updates to network infrastructure devices. You can use these features individually or together in a single Consul deployment.

> **Hands-on**: Complete the Getting Started tutorials to learn how to deploy Consul:
>
> - [Get Started on Kubernetes](/consul/tutorials/get-started-kubernetes)
> - [Get Started on VMs](/consul/tutorials/get-started-vms)
> - [HashiCorp Cloud Platform (HCP) Consul Dedicated](/consul/tutorials/get-started-hcp)

## [](/consul/docs/intro#how-does-consul-work) How does Consul work?

Consul provides a *control plane* that enables you to register, query, and secure services deployed across your network. The control plane is the part of the network infrastructure that maintains a central registry to track services and their respective IP addresses. It is a distributed system that runs on clusters of nodes, such as physical servers, cloud instances, virtual machines, or containers.

Consul interacts with the *data plane* through proxies. The data plane is the part of the network infrastructure that processes data requests.

![Basic Consul workflow](/_next/image?url=https%3A%2F%2Fcontent.hashicorp.com%2Fapi%2Fassets%3Fproduct%3Dconsul%26version%3Drefs%252Fheads%252Frelease%252F1.21.x%26asset%3Dwebsite%252Fpublic%252Fimg%252Fwhat-is-consul-overview-diagram.png%26width%3D1241%26height%3D625&w=3840&q=75&dpl=dpl_4PuvkBchyebFXaa5zmo81FAxj4Fs)

The core Consul workflow consists of the following stages:

- **Register**: Teams add services to the Consul catalog, which is a central registry that lets services automatically discover each other without requiring a human operator to modify application code, deploy additional load balancers, or hardcode IP addresses. It is the runtime source of truth for all services and their addresses. Teams can manually [define](/consul/docs/register/service/vm/define) and [register](/consul/docs/register/service/vm) using the CLI or the API, or you can automate the process in Kubernetes with [service sync](/consul/docs/register/service/k8s/service-sync). Services can also include health checks so that Consul can monitor for unhealthy services.
- **Query**: Consul’s identity-based DNS lets you find healthy services in the Consul catalog. Services registered with Consul provide health information, access points, and other data that help you control the flow of data through your network. Your services only access other services through their local proxy according to the identity-based policies you define.
- **Secure**: After services locate upstreams, Consul ensures that service-to-service communication is authenticated, authorized, and encrypted. Consul service mesh secures microservice architectures with mTLS and can allow or restrict access based on service identities, regardless of differences in compute environments and runtimes.

## [](/consul/docs/intro#why-consul) Why Consul?

Consul increases application resilience, bolsters uptime, accelerates application deployment, and improves security across service-to-service communications. HashiCorp co-founder and CTO Armon Dadgar explains how Consul solves networking challenges.

To learn more about Consul and how it compares to similar products, refer to [Consul use cases](/consul/docs/use-case).

To learn more about Consul and how it compares to similar products, refer to [Consul use cases](/consul/docs/use-case).

### [](/consul/docs/intro#automate-service-discovery) Automate service discovery

Adopting a microservices architecture on cloud infrastructure is a critical step toward delivering value at scale, but knowing where healthy services are running on your networks in real time becomes a challenge. Consul automates service discovery by replacing service connections usually handled with load balancers with an identity-based service catalog. The [service catalog](/consul/docs/concept/catalog) is a centralized source of truth that you can query through Consul’s DNS server or API. The catalog always knows which services are available, which have been removed, and which services are healthy.

To learn more about Consul ' s service discovery features and how they compares to similar products, refer to [Consul compared to other DNS tools](/consul/docs/use-case/dns).

### [](/consul/docs/intro#connect-services-across-runtimes-and-cloud-providers) Connect services across runtimes and cloud providers

Modern organizations may deploy services to a combination of on-prem infrastructure environments and public cloud providers across multiple regions. Services may run on bare metal, virtual machines, or as containers across Kubernetes clusters.

Consul routes network traffic to any runtime or infrastructure environment your services need to reach. You can also use Consul API Gateway to route traffic into and out of the network. Consul service mesh provides additional capabilities, such as securing communication between services, traffic management, and observability, with no application code changes.

Consul also has many integrations with Kubernetes that enable you to leverage Consul features in containerized environments. For example, Consul can automatically inject sidecar proxies into Kubernetes Pods and sync Kubernetes Services and non-Kubernetes services into the Consul service registry without manual changes to the application or changing the Pod definition.

You can also schedule Consul workloads with [HashiCorp Nomad](https://www.nomadproject.io/) to provide secure service-to-service communication between Nomad jobs and task groups.

### [](/consul/docs/intro#enable-zero-trust-network-security) Enable zero-trust network security

Microservice architectures are complex and difficult to secure against accidental disclosure to malicious actors. Consul provides several mechanisms that enhance network security without any changes to your application code, including mutual transport layer security (mTLS) encryption on all traffic between services and Consul intentions, which are service-to-service permissions that you can manage through the Consul UI, API, and CLI.

When you deploy Consul to Kubernetes clusters, you can also integrate with [HashiCorp Vault](https://www.vaultproject.io/) to manage sensitive data. By default, Consul on Kubernetes leverages Kubernetes secrets as the backend system. Kubernetes secrets are base64 encoded, unencrypted, and lack lease or time-to-live properties. By leveraging Vault as a secrets backend for Consul on Kubernetes, you can manage and store Consul related secrets within a centralized Vault cluster to use across one or many Consul on Kubernetes datacenters. Refer to [Vault as the Secrets Backend](/consul/docs/deploy/server/k8s/vault) for additional information.

You can also secure your Consul deployment, itself, by defining security policies in access control lists (ACL) to control access to data and Consul APIs.

### [](/consul/docs/intro#protect-your-services-against-network-failure) Protect your services against network failure

Outages are unavoidable, but with distributed systems it is critical that a power failure in one datacenter doesn’t disrupt downstream service operations. You can enable automated backups, redundancy zones, read-replicas, and other features that prevent data loss and downtime after a catastrophic event. L7 observability features also deliver service traffic metrics in the Consul UI, which help you understand the state of a service and its connections within the mesh.

### [](/consul/docs/intro#dynamically-update-network-infrastructure-devices) Dynamically update network infrastructure devices

Change to your network, including day-to-day operational tasks such as updating network device endpoints and firewall or load balancer rules, can lead to problems that disrupt operations at critical moments. You can deploy the Consul-Terraform-Sync (CTS) add-on to dynamically update network infrastructure devices when a service changes. CTS monitors the service information stored in Consul and automatically launches an instance of HashiCorp Terraform to drive relevant changes to the network infrastructure when Consul registers a change, reducing the manual effort of configuring network infrastructure.

### [](/consul/docs/intro#optimize-traffic-routes-for-deployment-and-testing-scenarios) Optimize traffic routes for deployment and testing scenarios

Rolling out changes can be risky, especially in complex network environments. Updated services may not behave as expected when connected to other services, resulting in upstream or downstream issues. Consul service mesh supports layer 7 (L7) traffic management, which lets you divide L7 traffic into different subsets of service instances. This enables you to divide your pool of services for canary testing, A/B tests, blue/green deployments, and soft multi-tenancy (prod/qa/staging sharing compute resources) deployments.

## [](/consul/docs/intro#consul-enterprise) Consul Enterprise

HashiCorp offers core Consul functionality for free in the community edition, which is ideal for smaller businesses and teams that want to pilot Consul within their organizations. As your business grows, you can upgrade to Consul Enterprise, which offers additional capabilities designed to address organizational complexities of collaboration, operations, scale, and governance.

### [](/consul/docs/intro#hcp-consul-dedicated) HCP Consul Dedicated

Warning

HCP Consul Dedicated will be retired on November 12, 2025. [Learn more in the HCP documentation](/hcp/docs/consul/migrate).

HashiCorp Cloud Platform (HCP) Consul is our SaaS that delivers Consul Enterprise capabilities and shifts the burden of managing the control plane to us. Create an HCP organization and leverage our expertise to simplify control plane maintenance and configuration. Learn more at [HashiCorp Cloud Platform](https://cloud.hashicorp.com/products/consul).

## [](/consul/docs/intro#community) Community

We welcome questions, suggestions, and contributions from the community.

- Ask questions in [HashiCorp Discuss](https://discuss.hashicorp.com/c/consul/29).
- Read our [contributing guide](https://github.com/hashicorp/consul/blob/main/.github/CONTRIBUTING.md).
- [Submit a Github issue](https://github.com/hashicorp/consul/issues/new/choose) for feature requests and bug reports.

[Edit this page on GitHub](https://github.com/hashicorp/consul/blob/main/website/content/docs/intro.mdx)
