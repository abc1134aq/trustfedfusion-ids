# Cross-Domain Schema Probe (2026-06-15)

Scope: local lightweight parquet copies only. This is schema/sample evidence, not final cross-domain performance.

| Dataset | Rows | Columns | Size MB | Label candidates | Flow-hint columns |
|---|---:|---:|---:|---|---|
| nf_ton_iot | 1157994 | 12 | 9.052 | Label; Attack | L4_SRC_PORT; L4_DST_PORT; PROTOCOL; IN_BYTES; OUT_BYTES; IN_PKTS; OUT_PKTS; TCP_FLAGS; FLOW_DURATION_MILLISECONDS |
| nf_bot_iot | 595376 | 12 | 2.147 | Label; Attack | L4_SRC_PORT; L4_DST_PORT; PROTOCOL; IN_BYTES; OUT_BYTES; IN_PKTS; OUT_PKTS; TCP_FLAGS; FLOW_DURATION_MILLISECONDS |
| unsw_nb15_train | 175341 | 36 | 9.172 | attack_cat; label | dur; proto; service; state; sbytes; dbytes; rate |
| unsw_nb15_test | 82332 | 36 | 4.329 | attack_cat; label | dur; proto; service; state; sbytes; dbytes; rate |

## Label Distributions (Top 20)

### nf_ton_iot

Label column candidate: `Label`
| Value | Count |
|---|---:|
| 1 | 959544 |
| 0 | 198450 |

Label column candidate: `Attack`
| Value | Count |
|---|---:|
| injection | 460812 |
| Benign | 198450 |
| ddos | 197680 |
| password | 144792 |
| xss | 99913 |
| scanning | 20618 |
| backdoor | 17243 |
| dos | 17056 |
| mitm | 1288 |
| ransomware | 142 |

### nf_bot_iot

Label column candidate: `Label`
| Value | Count |
|---|---:|
| 1 | 581573 |
| 0 | 13803 |

Label column candidate: `Attack`
| Value | Count |
|---|---:|
| Reconnaissance | 467215 |
| DDoS | 56260 |
| DoS | 56249 |
| Benign | 13803 |
| Theft | 1849 |

### unsw_nb15_train

Label column candidate: `attack_cat`
| Value | Count |
|---|---:|
| Normal | 56000 |
| Generic | 40000 |
| Exploits | 33393 |
| Fuzzers | 18184 |
| DoS | 12264 |
| Reconnaissance | 10491 |
| Analysis | 2000 |
| Backdoor | 1746 |
| Shellcode | 1133 |
| Worms | 130 |

Label column candidate: `label`
| Value | Count |
|---|---:|
| 1 | 119341 |
| 0 | 56000 |

### unsw_nb15_test

Label column candidate: `attack_cat`
| Value | Count |
|---|---:|
| Normal | 37000 |
| Generic | 18871 |
| Exploits | 11132 |
| Fuzzers | 6062 |
| DoS | 4089 |
| Reconnaissance | 3496 |
| Analysis | 677 |
| Backdoor | 583 |
| Shellcode | 378 |
| Worms | 44 |

Label column candidate: `label`
| Value | Count |
|---|---:|
| 1 | 45332 |
| 0 | 37000 |

## Immediate Use
- UNSW-NB15 is small enough for local schema/sample experiments and has explicit attack category columns.
- NF-ToN/NF-BoT use NetFlow-style fields and are good next cross-domain probes for traffic-only transfer and CTI feature availability stress tests.
- None of these rows should be merged into the Edge-IIoT main training result without a separate cross-domain protocol.
