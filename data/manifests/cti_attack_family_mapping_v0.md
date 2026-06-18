# CTI / Attack-Family Mapping v0

当前方法名: TrustFedFusion-IDS  
更新日期: 2026-06-15

## 用途边界

这个映射表第一阶段只用于:

1. 构造 attack-family non-IID 客户端。
2. 构造 unknown attack / leave-one-family-out 测试。
3. 建立 Threat Intelligence Graph Adapter 的 schema。
4. 做错误 CTI 映射/情报误导的鲁棒性实验。

**不要直接把真实标签映射结果作为训练输入**，否则会产生标签泄露。后续可用可观测字段如 protocol、port、flow statistics、log keywords、IOC feeds 来生成弱 CTI 证据。

## Edge-IIoTset / ML-EdgeIIoT 标签映射

| 原始标签 | 威胁家族 | 可能 ATT&CK/CTI 语义 | 备注 |
| --- | --- | --- | --- |
| Normal | Benign | Benign operation | 正常类 |
| DDoS_UDP | DoS/DDoS | Network DoS, UDP flood | 可归入 flooding |
| DDoS_ICMP | DoS/DDoS | Network DoS, ICMP flood | 可归入 flooding |
| DDoS_TCP | DoS/DDoS | SYN/TCP flood | 可归入 flooding |
| DDoS_HTTP | DoS/DDoS | Application-layer flood | HTTP 层 |
| DDoS | DoS/DDoS | Denial of service | balanced subset 粗标签 |
| DoS | DoS/DDoS | Denial of service | balanced subset 粗标签 |
| MITM | Man-in-the-middle | ARP/DNS spoofing, traffic interception | 可连接 spoofing/credential exposure |
| Fingerprinting | Reconnaissance | OS/service fingerprinting | 信息收集 |
| Port_Scanning | Reconnaissance | Port/service scanning | 信息收集 |
| Vulnerability_scanner | Reconnaissance | Vulnerability discovery | 信息收集 |
| Password | Credential attack | Password guessing/brute force | 凭证攻击 |
| SQL_injection | Injection | SQL injection | Web/app injection |
| XSS | Injection | Cross-site scripting | Web/app injection |
| Uploading | Injection/Exfiltration | Malicious upload or data movement | 需精读数据说明确认 |
| Backdoor | Malware/Persistence | Backdoor/persistence | 恶意软件/持久化 |
| Ransomware | Malware/Impact | Ransomware/impact | 影响/勒索 |
| Injection | Injection | Generic injection | balanced subset 粗标签 |

## Graph schema v0

| 节点类型 | 示例 | 来源 |
| --- | --- | --- |
| Client | organization/device/client id | 联邦划分 |
| Evidence source | traffic, logs, system resources, CTI | P01 多源特征描述 |
| Observable | protocol, port, packet rate, flow duration | 数据集字段 |
| Threat family | DoS/DDoS, Reconnaissance, Injection, MITM, Malware | 本映射 |
| Technique | UDP flood, SQL injection, port scanning | CTI 映射 |
| Label | 原始数据集攻击标签 | 仅监督信号/评估 |

## 计划中的 CTI 证据生成

| 证据 | 是否泄露标签 | 可用性 | 说明 |
| --- | --- | --- | --- |
| 由真实标签直接映射 attack family | 是 | 仅评估/划分 | 不能作为模型输入 |
| 由端口/协议映射弱 CTI hint | 否 | 可作为输入 | 如 Modbus/HTTP/DNS/ICMP/TCP/UDP |
| 由流量统计异常映射 weak technique | 否 | 可作为输入 | 如 high rate + UDP -> flood hint |
| 由外部 IOC feed 映射 | 否 | 后续增强 | 需要公开 IOC 数据 |
| 随机扰动 CTI edge | 否 | 鲁棒实验 | 模拟 threat-intelligence poisoning |

## 实验切分建议

1. Leave-one-family-out: 留出 Reconnaissance 或 Injection 做未知攻击。
2. Client label skew: 每个客户端集中 1-2 个 attack family。
3. CTI poisoning: 随机重连 10%-30% threat-family/technique edges。
4. Source dropout: 随机去掉 CTI 或 log evidence，测 fusion robustness。
