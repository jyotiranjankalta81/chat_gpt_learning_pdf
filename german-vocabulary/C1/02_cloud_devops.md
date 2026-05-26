# C1 — Cloud Computing & DevOps (Cloud-Computing & DevOps)

> ~130 entries covering enterprise cloud architecture, DevOps practices, SRE, platform engineering, and production operations vocabulary for IT professionals in Germany.

---

## Section 1: Cloud Architecture (Cloud-Architektur)

| # | German | English | Pronunciation | Article | PoS | Example (DE) | Example (EN) | Context | Plural / Conj. | Collocations | Synonyms | Opposites |
|---|--------|---------|---------------|---------|-----|-------------|-------------|---------|----------------|-------------|----------|----------|
| 1 | Cloud-native Architektur | cloud-native architecture | klowd-neh-tiv-ar-khee-tek-toor | die | n. | Cloud-native Architektur nutzt alle Cloud-Vorteile. | Cloud-native architecture uses all cloud advantages. | Cloud | — | — | — | legacy Architektur |
| 2 | Microservices-Architektur | microservices architecture | my-kroh-zer-vi-ses-ar-khee-tek-toor | die | n. | Die Microservices-Architektur ermöglicht unabhängige Deployments. | Microservices architecture enables independent deployments. | Cloud | — | — | — | monolithische Architektur |
| 3 | Service Mesh | service mesh | zer-vis-mesh | das | n. | Ein Service Mesh verwaltet die Kommunikation zwischen Services. | A service mesh manages communication between services. | Cloud | — | Istio, Linkerd | — | — |
| 4 | API-Gateway | API gateway | ah-pee-eye-gayt-vay | das | n. | Das API-Gateway bündelt alle API-Aufrufe. | The API gateway bundles all API calls. | Cloud | API-Gateways | — | — | direkte API-Kommunikation |
| 5 | Lastverteilung | load balancing | last-fer-ty-loong | die | n. | Die Lastverteilung verhindert Überlastung. | Load balancing prevents overload. | Cloud | — | — | Load Balancing | — |
| 6 | Auto-Scaling | auto-scaling | ow-toh-skeh-ling | das | n. | Auto-Scaling passt Ressourcen automatisch an. | Auto-scaling automatically adjusts resources. | Cloud | — | horizontales/vertikales Auto-Scaling | — | manuelle Skalierung |
| 7 | Verfügbarkeitszonen | availability zones | fer-fyoog-bar-kyts-tsoh-nen | — | n. (pl.) | Wir nutzen drei Verfügbarkeitszonen für Ausfallsicherheit. | We use three availability zones for fault tolerance. | Cloud | — | — | — | — |
| 8 | Multi-Region-Deployment | multi-region deployment | mol-tee-reh-gee-ohn-deh-ploy-ment | das | n. | Multi-Region-Deployment reduziert Latenz weltweit. | Multi-region deployment reduces latency worldwide. | Cloud | — | — | — | Single-Region |
| 9 | Chaos Engineering | chaos engineering | keh-os-en-ji-nee-ring | das | n. | Chaos Engineering testet die Resilienz des Systems. | Chaos engineering tests system resilience. | Cloud | — | Chaos Monkey | — | — |
| 10 | Disaster Recovery | disaster recovery | dih-zas-ter-ri-ko-ve-ree | das | n. | Der Disaster Recovery Plan muss getestet werden. | The disaster recovery plan must be tested. | Cloud | — | DR-Plan, RTO, RPO | — | normale Betriebsführung |
| 11 | RTO (Recovery Time Objective) | RTO | er-teh-oh | das | n. | Das RTO beträgt 4 Stunden. | The RTO is 4 hours. | Cloud | — | — | — | — |
| 12 | RPO (Recovery Point Objective) | RPO | er-peh-oh | das | n. | Das RPO beträgt 1 Stunde. | The RPO is 1 hour. | Cloud | — | — | — | — |
| 13 | Blue/Green Deployment | blue/green deployment | bloo-green-deh-ploy-ment | das | n. | Blue/Green Deployment ermöglicht unterbrechungsfreie Releases. | Blue/green deployment enables seamless releases. | Cloud/DevOps | — | — | — | — |
| 14 | Canary Deployment | canary deployment | keh-neh-ree-deh-ploy-ment | das | n. | Canary Deployment rollt Updates schrittweise aus. | Canary deployment rolls out updates gradually. | Cloud/DevOps | — | — | — | — |
| 15 | Feature Flags | feature flags | fee-tschur-fleks | — | n. (pl.) | Feature Flags erlauben kontrollierten Funktionsrollout. | Feature flags allow controlled feature rollout. | Cloud/DevOps | — | — | Feature Toggle | — |

---

## Section 2: DevOps Culture & Practices

| # | German | English | Pronunciation | Article | PoS | Example (DE) | Example (EN) | Context | Plural / Conj. | Collocations | Synonyms | Opposites |
|---|--------|---------|---------------|---------|-----|-------------|-------------|---------|----------------|-------------|----------|----------|
| 16 | DevOps-Kultur | DevOps culture | dev-ops-kool-toor | die | n. | Eine echte DevOps-Kultur überwindet Silodenken. | A true DevOps culture overcomes silo thinking. | DevOps | — | — | — | Silokultur |
| 17 | gemeinsame Verantwortung | shared responsibility | geh-myne-zah-meh fer-ant-vor-toong | die | n. | DevOps bedeutet gemeinsame Verantwortung für Code und Betrieb. | DevOps means shared responsibility for code and operations. | DevOps | — | — | — | — |
| 18 | Feedback-Schleifen | feedback loops | feed-bek-shly-fen | — | n. (pl.) | Kurze Feedback-Schleifen beschleunigen die Entwicklung. | Short feedback loops accelerate development. | DevOps | — | — | — | lange Feedback-Zyklen |
| 19 | Shift Left | shift left | shift-left | das | n. | Shift Left verlagert Tests früher in den Entwicklungsprozess. | Shift left moves testing earlier in the development process. | DevOps | — | — | — | — |
| 20 | Versionskontrolle | version control | fer-zee-ohns-kon-troh-leh | die | n. | Alles in Versionskontrolle — auch Konfiguration. | Everything in version control — including configuration. | DevOps | — | Git, SVN | — | — |
| 21 | Code-Review | code review | koht-ri-vyoo | das | n. | Code-Reviews verbessern die Codequalität. | Code reviews improve code quality. | DevOps | Code-Reviews | Pull Request, Merge Request | — | — |
| 22 | Pull Request (PR) | pull request | pool-ri-kvest | der | n. | Ich erstelle einen Pull Request für das Feature. | I create a pull request for the feature. | DevOps | Pull Requests | PR reviewen, PR mergen | — | — |
| 23 | Merge | merge | merdzh | das | n. | Der Merge in main erfolgt nach Review. | The merge into main happens after review. | DevOps | — | mergen, Merge-Konflikt | — | — |
| 24 | Branching-Strategie | branching strategy | bran-tshing-shtra-teh-ghee | die | n. | GitFlow ist eine Branching-Strategie. | GitFlow is a branching strategy. | DevOps | — | Gitflow, Trunk-Based Development | — | — |
| 25 | technische Schulden | technical debt | tekh-nish-eh shool-den | — | n. (pl.) | Technische Schulden müssen aktiv abgebaut werden. | Technical debt must be actively reduced. | DevOps | — | Tech Debt | — | sauberer Code |
| 26 | Refactoring | refactoring | ree-fak-to-ring | das | n. | Refactoring verbessert die Codequalität ohne neue Features. | Refactoring improves code quality without new features. | Development | — | Code refactoren | — | neue Features |
| 27 | Test-Driven Development (TDD) | TDD | teh-deh-deh | das | n. | TDD schreibt Tests vor dem Code. | TDD writes tests before the code. | Development | — | — | testgetriebene Entwicklung | — |
| 28 | Behaviour-Driven Development (BDD) | BDD | beh-deh-deh | das | n. | BDD beschreibt Verhalten aus Benutzersicht. | BDD describes behaviour from the user's perspective. | Development | — | Gherkin, Cucumber | — | — |
| 29 | Acceptance Testing | acceptance testing | ak-sep-tans-tes-ting | das | n. | Acceptance Testing verifiziert die Anforderungen. | Acceptance testing verifies requirements. | Development | — | — | Abnahmetesting | — |
| 30 | Smoke Test | smoke test | smohk-test | der | n. | Nach jedem Deploy führen wir Smoke Tests durch. | After each deploy we run smoke tests. | DevOps | Smoke Tests | — | — | vollständige Testsuiten |

---

## Section 3: Site Reliability Engineering (SRE)

| # | German | English | Pronunciation | Article | PoS | Example (DE) | Example (EN) | Context | Plural / Conj. | Collocations | Synonyms | Opposites |
|---|--------|---------|---------------|---------|-----|-------------|-------------|---------|----------------|-------------|----------|----------|
| 31 | Site Reliability Engineering (SRE) | SRE | es-ar-ee | das | n. | SRE verbindet Software-Engineering mit Betrieb. | SRE combines software engineering with operations. | SRE | — | — | Zuverlässigkeits-Engineering | — |
| 32 | Service Level Agreement (SLA) | SLA | es-el-ah | das | n. | Das SLA garantiert 99,9% Verfügbarkeit. | The SLA guarantees 99.9% availability. | SRE | SLAs | — | Dienstgütevereinbarung | — |
| 33 | Service Level Objective (SLO) | SLO | es-el-oh | das | n. | Das SLO definiert interne Verfügbarkeitsziele. | The SLO defines internal availability targets. | SRE | SLOs | — | — | SLA (external) |
| 34 | Service Level Indicator (SLI) | SLI | es-el-ee | das | n. | SLIs messen die tatsächliche Systemleistung. | SLIs measure actual system performance. | SRE | SLIs | — | — | — |
| 35 | Error Budget | error budget | eh-ror-boo-dzhit | das | n. | Das Error Budget bestimmt, wann Deployments riskant sind. | The error budget determines when deployments are risky. | SRE | Error Budgets | — | Fehlerkontingent | — |
| 36 | Toil | toil (SRE term) | toyl | das | n. | Toil sind manuelle, repetitive Tätigkeiten. | Toil refers to manual, repetitive tasks. | SRE | — | Toil reduzieren | — | Automatisierung |
| 37 | Postmortem | postmortem | pohst-mor-tem | das | n. | Nach jedem Ausfall schreiben wir ein Postmortem. | After every outage we write a postmortem. | SRE | Postmortems | blameless Postmortem | — | — |
| 38 | blameless Postmortem | blameless postmortem | bley-mes-pohst-mor-tem | das | n. | Blameless Postmortems fokussieren auf Systemverbesserung. | Blameless postmortems focus on system improvement. | SRE | — | — | — | Schuldzuweisung |
| 39 | Incident Management | incident management | in-tsi-dent-ma-neh-jment | das | n. | Gutes Incident Management minimiert Downtime. | Good incident management minimises downtime. | SRE | — | — | Vorfallmanagement | — |
| 40 | On-Call | on-call | on-kohl | das | n. | Ich habe diese Woche On-Call-Bereitschaft. | I am on call this week. | SRE | — | On-Call-Rotationen | Bereitschaftsdienst | — |
| 41 | Runbook | runbook | ron-bookh | das | n. | Das Runbook beschreibt die Reaktion auf Vorfälle. | The runbook describes the response to incidents. | SRE | Runbooks | — | — | — |
| 42 | Playbook | playbook | pley-bookh | das | n. | Das Playbook enthält bewährte Lösungen. | The playbook contains proven solutions. | SRE | Playbooks | — | — | — |
| 43 | Monitoring | monitoring | mo-ni-to-ring | das | n. | Gutes Monitoring erkennt Probleme früh. | Good monitoring detects problems early. | SRE | — | Alerting, Observability | Überwachung | — |
| 44 | Observability | observability | ob-zer-vah-bil-i-tee | die | n. | Observability umfasst Metriken, Logs und Traces. | Observability includes metrics, logs and traces. | SRE | — | Traces, Logs, Metrics | — | — |
| 45 | Distributed Tracing | distributed tracing | dis-tri-byoo-ted-trey-sing | das | n. | Distributed Tracing verfolgt Anfragen durch Microservices. | Distributed tracing follows requests through microservices. | SRE | — | Jaeger, Zipkin | — | — |

---

## Section 4: Kubernetes & Container Orchestration

| # | German | English | Pronunciation | Article | PoS | Example (DE) | Example (EN) | Context | Plural / Conj. | Collocations | Synonyms | Opposites |
|---|--------|---------|---------------|---------|-----|-------------|-------------|---------|----------------|-------------|----------|----------|
| 46 | Pod | pod (Kubernetes) | pot | der | n. | Ein Pod enthält einen oder mehrere Container. | A pod contains one or more containers. | Kubernetes | Pods | — | — | — |
| 47 | Deployment | deployment (K8s) | deh-ploy-ment | das | n. | Das Kubernetes Deployment verwaltet Replikas. | The Kubernetes Deployment manages replicas. | Kubernetes | Deployments | — | — | — |
| 48 | Service (K8s) | service (K8s) | zer-vis | der | n. | Der Kubernetes Service exponiert Pods. | The Kubernetes Service exposes pods. | Kubernetes | Services | ClusterIP, NodePort, LoadBalancer | — | — |
| 49 | Namespace | namespace | nehm-shpeys | der | n. | Namespaces isolieren Workloads. | Namespaces isolate workloads. | Kubernetes | Namespaces | — | — | — |
| 50 | ConfigMap | ConfigMap | kon-fig-map | die | n. | ConfigMaps speichern nicht-sensitive Konfigurationen. | ConfigMaps store non-sensitive configurations. | Kubernetes | ConfigMaps | — | — | Secret |
| 51 | Secret | secret (K8s) | see-kret | das | n. | Secrets speichern sensible Daten verschlüsselt. | Secrets store sensitive data encrypted. | Kubernetes | Secrets | — | — | ConfigMap |
| 52 | Ingress | ingress | in-gres | der | n. | Der Ingress-Controller routet externen Traffic. | The Ingress controller routes external traffic. | Kubernetes | Ingresses | — | — | — |
| 53 | Horizontal Pod Autoscaler (HPA) | HPA | hah-peh-ah | der | n. | HPA skaliert Pods basierend auf CPU-Auslastung. | HPA scales pods based on CPU utilisation. | Kubernetes | HPAs | — | — | — |
| 54 | StatefulSet | StatefulSet | stehyt-fool-set | das | n. | StatefulSets verwalten zustandsbehaftete Anwendungen. | StatefulSets manage stateful applications. | Kubernetes | StatefulSets | — | — | Deployment (stateless) |
| 55 | Persistent Volume (PV) | persistent volume | per-sis-tent-voh-loo-men | das | n. | Persistent Volumes speichern Daten über Pod-Neustarts hinaus. | Persistent volumes store data beyond pod restarts. | Kubernetes | Persistent Volumes | PVC | — | ephemeral storage |
| 56 | Helm | Helm | helm | das | n. | Helm ist der Paketmanager für Kubernetes. | Helm is the package manager for Kubernetes. | Kubernetes | — | Helm Chart | — | — |
| 57 | Operator Pattern | operator pattern | o-pe-reh-tor-pa-tern | das | n. | Kubernetes Operator automatisiert komplexe Aufgaben. | A Kubernetes operator automates complex tasks. | Kubernetes | — | — | — | — |
| 58 | Service Mesh (Istio) | service mesh | zer-vis-mesh | das | n. | Istio implementiert ein Service Mesh. | Istio implements a service mesh. | Kubernetes | — | mTLS, Envoy Proxy | — | — |

---

## Section 5: CI/CD & Pipeline Management

| # | German | English | Pronunciation | Article | PoS | Example (DE) | Example (EN) | Context | Plural / Conj. | Collocations | Synonyms | Opposites |
|---|--------|---------|---------------|---------|-----|-------------|-------------|---------|----------------|-------------|----------|----------|
| 59 | Deployment-Pipeline | deployment pipeline | deh-ploy-ment-pipe-line | die | n. | Die Deployment-Pipeline automatisiert den Release-Prozess. | The deployment pipeline automates the release process. | CI/CD | Deployment-Pipelines | — | — | manuelles Deployment |
| 60 | Build-Artefakt | build artefact | bilt-ar-teh-fakt | das | n. | Build-Artefakte werden in einer Registry gespeichert. | Build artefacts are stored in a registry. | CI/CD | Build-Artefakte | — | — | — |
| 61 | Docker Registry | container registry | dok-er-reh-gi-stree | die | n. | Images werden in der Docker Registry gespeichert. | Images are stored in the Docker Registry. | CI/CD | — | — | Container Registry | — |
| 62 | Image | container image | i-midzh | das | n. | Das Docker Image enthält alles für die App. | The Docker image contains everything for the app. | CI/CD | Images | Image bauen, Image pushen | — | — |
| 63 | Rollback | rollback | rohl-bek | das | n. | Bei einem Fehler führen wir einen Rollback durch. | In case of an error we perform a rollback. | CI/CD | Rollbacks | — | — | Rollforward |
| 64 | Staging-Umgebung | staging environment | steh-dzhing-oom-geh-boong | die | n. | Wir testen in der Staging-Umgebung. | We test in the staging environment. | CI/CD | Staging-Umgebungen | — | — | Produktionsumgebung |
| 65 | Produktionsumgebung | production environment | pro-dook-tsee-ohns-oom-geh-boong | die | n. | Nur getesteter Code kommt in die Produktion. | Only tested code goes into production. | CI/CD | — | — | Prod | Entwicklungsumgebung |
| 66 | Umgebungsvariable | environment variable | oom-geh-boongs-vah-ree-ah-bleh | die | n. | Secrets werden als Umgebungsvariablen gesetzt. | Secrets are set as environment variables. | CI/CD | Umgebungsvariablen | ENV-Variable | — | — |
| 67 | Artefakt-Repository | artifact repository | ar-teh-fakt-reh-poh-zi-toh-ree | das | n. | Nexus ist ein Artefakt-Repository. | Nexus is an artifact repository. | CI/CD | — | Nexus, Artifactory | — | — |
| 68 | Release-Management | release management | reh-lees-ma-neh-jment | das | n. | Release-Management koordiniert neue Versionen. | Release management coordinates new versions. | CI/CD | — | — | — | — |

---

## Section 6: Cloud Security & Compliance

| # | German | English | Pronunciation | Article | PoS | Example (DE) | Example (EN) | Context | Plural / Conj. | Collocations | Synonyms | Opposites |
|---|--------|---------|---------------|---------|-----|-------------|-------------|---------|----------------|-------------|----------|----------|
| 69 | Datensouveränität | data sovereignty | dah-ten-zoo-veh-reh-ni-teht | die | n. | Datensouveränität ist in Europa gesetzlich geregelt. | Data sovereignty is legally regulated in Europe. | Cloud/Legal | — | — | — | — |
| 70 | DSGVO-Konformität | GDPR compliance | deh-es-geh-fow-kon-for-mi-teht | die | n. | Alle Cloud-Dienste müssen DSGVO-konform sein. | All cloud services must be GDPR-compliant. | Cloud/Legal | — | — | — | — |
| 71 | Verschlüsselung at rest | encryption at rest | fer-shlys-el-oong-at-rest | die | n. | Daten werden verschlüsselt at rest gespeichert. | Data is stored encrypted at rest. | Cloud Security | — | — | — | unverschlüsselte Speicherung |
| 72 | Verschlüsselung in transit | encryption in transit | fer-shlys-el-oong-in-tran-sit | die | n. | TLS verschlüsselt Daten in transit. | TLS encrypts data in transit. | Cloud Security | — | TLS, SSL | — | unverschlüsselte Übertragung |
| 73 | IAM (Identity and Access Management) | IAM | ee-ah-em | das | n. | IAM kontrolliert, wer was in der Cloud tun darf. | IAM controls who can do what in the cloud. | Cloud Security | — | — | Identitätsmanagement | — |
| 74 | Least Privilege Prinzip | principle of least privilege | leest-pri-vi-lezh-prin-tsip | das | n. | Das Least Privilege Prinzip minimiert Sicherheitsrisiken. | The principle of least privilege minimises security risks. | Cloud Security | — | — | minimales Berechtigungsprinzip | — |
| 75 | Netzwerksegmentierung | network segmentation | nets-vehrk-zeg-men-tee-roong | die | n. | Netzwerksegmentierung isoliert kritische Systeme. | Network segmentation isolates critical systems. | Cloud Security | — | — | — | — |
| 76 | Security as Code | security as code | si-kyoo-ri-tee-as-koht | das | n. | Security as Code integriert Sicherheit früh. | Security as Code integrates security early. | Cloud Security | — | — | — | manuelle Sicherheitschecks |
| 77 | Schwachstellen-Scan | vulnerability scan | shvakh-shtel-en-skan | der | n. | Regelmäßige Schwachstellen-Scans sind Pflicht. | Regular vulnerability scans are mandatory. | Cloud Security | Schwachstellen-Scans | — | Vulnerability Assessment | — |
| 78 | CVE (Common Vulnerabilities and Exposures) | CVE | tseh-veh-eh | das | n. | Dieses CVE betrifft kritische Infrastruktur. | This CVE affects critical infrastructure. | Cloud Security | CVEs | — | — | — |

---

## Section 7: Observability & Monitoring

| # | German | English | Pronunciation | Article | PoS | Example (DE) | Example (EN) | Context | Plural / Conj. | Collocations | Synonyms | Opposites |
|---|--------|---------|---------------|---------|-----|-------------|-------------|---------|----------------|-------------|----------|----------|
| 79 | Metriken | metrics | meh-tri-ken | — | n. (pl.) | Wir sammeln Metriken mit Prometheus. | We collect metrics with Prometheus. | Observability | — | — | Kennzahlen | — |
| 80 | Logs | logs | logs | — | n. (pl.) | Logs werden in Elasticsearch gespeichert. | Logs are stored in Elasticsearch. | Observability | — | Log-Aggregation | Protokolldateien | — |
| 81 | Traces | traces | trey-ses | — | n. (pl.) | Traces zeigen den Weg einer Anfrage. | Traces show the path of a request. | Observability | — | Distributed Tracing | Ablaufverfolgung | — |
| 82 | Alert | alert | ah-lert | der | n. | Der Alert wurde um 3 Uhr getriggert. | The alert was triggered at 3 AM. | Monitoring | Alerts | — | Alarm, Benachrichtigung | — |
| 83 | Dashboard | dashboard | dash-bort | das | n. | Das Grafana-Dashboard zeigt alle Metriken. | The Grafana dashboard shows all metrics. | Monitoring | Dashboards | — | — | — |
| 84 | SLI/SLO-Tracking | SLI/SLO tracking | es-el-ee/es-el-oh-trek-ing | das | n. | Kontinuierliches SLI/SLO-Tracking verhindert SLA-Verletzungen. | Continuous SLI/SLO tracking prevents SLA violations. | SRE | — | — | — | — |
| 85 | MTTR (Mean Time to Recovery) | MTTR | em-teh-teh-er | der | n. | Ein gutes Team hat eine niedrige MTTR. | A good team has a low MTTR. | SRE | — | — | mittlere Wiederherstellungszeit | — |
| 86 | MTTD (Mean Time to Detection) | MTTD | em-teh-teh-deh | der | n. | Eine niedrige MTTD verbessert die Reaktionsfähigkeit. | A low MTTD improves responsiveness. | SRE | — | — | mittlere Erkennungszeit | — |
| 87 | Anomalieerkennung | anomaly detection | ah-noh-mah-lee-er-ken-noong | die | n. | KI-gestützte Anomalieerkennung findet Probleme früh. | AI-supported anomaly detection finds problems early. | Monitoring | — | — | — | — |

---

## Section 8: Platform Engineering & Developer Experience

| # | German | English | Pronunciation | Article | PoS | Example (DE) | Example (EN) | Context | Plural / Conj. | Collocations | Synonyms | Opposites |
|---|--------|---------|---------------|---------|-----|-------------|-------------|---------|----------------|-------------|----------|----------|
| 88 | Internal Developer Platform | internal developer platform | in-ter-nahl-deh-vel-oh-per-plat-form | die | n. | Eine IDP verbessert die Developer Experience. | An IDP improves the developer experience. | Platform | — | — | IDP | — |
| 89 | Developer Experience (DX) | developer experience | deh-vel-oh-per-eks-peh-ree-ens | die | n. | Gute DX steigert die Produktivität. | Good DX increases productivity. | Platform | — | — | Entwicklererfahrung | — |
| 90 | Golden Path | golden path | gohl-den-path | der | n. | Der Golden Path bietet empfohlene Toolchains. | The golden path provides recommended toolchains. | Platform | — | — | — | — |
| 91 | Self-Service-Infrastruktur | self-service infrastructure | self-zer-vis-in-frah-shtrook-toor | die | n. | Self-Service-Infrastruktur reduziert Abhängigkeiten. | Self-service infrastructure reduces dependencies. | Platform | — | — | — | manuelle Infrastrukturbereitstellung |
| 92 | Backstage | Backstage | bek-steydzh | — | n. | Backstage ist ein Open-Source-Portal für Developer. | Backstage is an open-source portal for developers. | Platform | — | — | Developer Portal | — |
| 93 | GitOps | GitOps | git-ops | das | n. | GitOps verwendet Git als einzige Quelle der Wahrheit. | GitOps uses Git as the single source of truth. | DevOps | — | ArgoCD, Flux | — | — |
| 94 | ArgoCD | ArgoCD | ar-go-tseh-deh | — | n. | ArgoCD implementiert GitOps für Kubernetes. | ArgoCD implements GitOps for Kubernetes. | DevOps | — | — | — | — |
| 95 | Crossplane | Crossplane | kros-pleyn | — | n. | Crossplane verwaltet Cloud-Ressourcen als Kubernetes-Objekte. | Crossplane manages cloud resources as Kubernetes objects. | Platform | — | — | — | — |

---

## Section 9: German IT Workplace Vocabulary (C1)

| # | German | English | Pronunciation | Article | PoS | Example (DE) | Example (EN) | Context | Plural / Conj. | Collocations | Synonyms | Opposites |
|---|--------|---------|---------------|---------|-----|-------------|-------------|---------|----------------|-------------|----------|----------|
| 96 | IT-Betrieb | IT operations | ee-teh-beh-treep | der | n. | Der IT-Betrieb ist für die Systemverfügbarkeit zuständig. | IT operations is responsible for system availability. | IT Work | — | — | Operations | Entwicklung |
| 97 | technische Leitung | technical leadership | tekh-nish-eh ly-toong | die | n. | Die technische Leitung entscheidet über die Architektur. | Technical leadership decides on architecture. | IT Work | — | — | Tech Lead | — |
| 98 | Architekturentscheidung | architectural decision | ar-khee-tek-toor-ent-shy-doong | die | n. | Architekturentscheidungen haben langfristige Auswirkungen. | Architectural decisions have long-term consequences. | IT Work | Architekturentscheidungen | ADR (Architecture Decision Record) | — | — |
| 99 | Sprint-Retrospektive | sprint retrospective | shprint-reh-troh-spek-tee-veh | die | n. | Die Sprint-Retrospektive verbessert den Prozess kontinuierlich. | The sprint retrospective continuously improves the process. | Agile | Sprint-Retrospektiven | — | Retro | — |
| 100 | Velocity | velocity (agile) | veh-loh-tsi-tee | die | n. | Die Team-Velocity verbessert sich über Zeit. | Team velocity improves over time. | Agile | — | — | Teamgeschwindigkeit | — |
