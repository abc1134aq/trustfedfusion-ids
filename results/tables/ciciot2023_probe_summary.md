# CICIoT2023 Probe Summary

Source kernel: `<kaggle-user>/trustfedfusion-ciciot2023-probe`.

## Probe result

- Files inspected: 30; successful: 30.
- Total inspected file size: 2060.1 MB.
- Estimated rows across inspected small files: 7,332,065.
- Columns per inspected part: 47.
- Detected label column: `label`.
- Full dataset was not downloaded locally; only probe outputs were pulled back.

## First-file columns

`flow_duration`, `Header_Length`, `Protocol Type`, `Duration`, `Rate`, `Srate`, `Drate`, `fin_flag_number`, `syn_flag_number`, `rst_flag_number`, `psh_flag_number`, `ack_flag_number`, `ece_flag_number`, `cwr_flag_number`, `ack_count`, `syn_count`, `fin_count`, `urg_count`, `rst_count`, `HTTP`, `HTTPS`, `DNS`, `Telnet`, `SMTP`, `SSH`, `IRC`, `TCP`, `UDP`, `DHCP`, `ARP`, `ICMP`, `IPv`, `LLC`, `Tot sum`, `Min`, `Max`, `AVG`, `Std`, `Tot size`, `IAT`, `Number`, `Magnitue`, `Radius`, `Covariance`, `Variance`, `Weight`, `label`

## Bounded label distribution

| label | bounded_count_first_rows |
| --- | --- |
| DDoS-ICMP_Flood | 232167 |
| DDoS-UDP_Flood | 174751 |
| DDoS-TCP_Flood | 144200 |
| DDoS-PSHACK_Flood | 131784 |
| DDoS-SYN_Flood | 129798 |
| DDoS-RSTFINFlood | 129480 |
| DDoS-SynonymousIP_Flood | 115926 |
| DoS-UDP_Flood | 105949 |
| DoS-TCP_Flood | 85346 |
| DoS-SYN_Flood | 65134 |
| BenignTraffic | 35053 |
| Mirai-greeth_flood | 31856 |
| Mirai-udpplain | 28795 |
| Mirai-greip_flood | 24440 |
| DDoS-ICMP_Fragmentation | 14341 |
| MITM-ArpSpoofing | 9886 |
| DDoS-UDP_Fragmentation | 9379 |
| DDoS-ACK_Fragmentation | 9253 |
| DNS_Spoofing | 5859 |
| Recon-HostDiscovery | 4308 |
| Recon-OSScan | 3166 |
| Recon-PortScan | 2563 |
| DoS-HTTP_Flood | 2351 |
| VulnerabilityScan | 1160 |
| DDoS-HTTP_Flood | 951 |
| DDoS-SlowLoris | 790 |
| DictionaryBruteForce | 417 |
| SqlInjection | 188 |
| BrowserHijacking | 184 |
| CommandInjection | 177 |

## Cross-domain implication

- CICIoT2023 is usable as a Kaggle-side cross-domain target with 47 tabular columns and a `label` target.
- Schema differs from Edge-IIoT, so the next experiment should use a schema-normalized tabular baseline and family-level mapping, not raw feature reuse.
- Because the inspected rows are bounded, these label counts are for planning only, not final dataset statistics.
