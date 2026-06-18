# GitHub / Zenodo 快速上传说明

当前目录是 TrustFedFusion-IDS 的 GitHub 仓库 staging 目录，可直接作为 GitHub 仓库内容上传。

## 1. 推荐 GitHub 仓库设置

- Repository name: `trustfedfusion-ids`
- Visibility: 投稿前可先设为 Private；需要公开 DOI 时再设为 Public
- Description: `Reproducibility package for TrustFedFusion-IDS, a reliability-aware federated threat-evidence fusion framework for cross-domain intrusion detection in critical infrastructure.`
- Licence: MIT

## 2. 推荐 Zenodo 设置

如果用 GitHub + Zenodo:

1. 在 GitHub 创建仓库并上传本目录全部内容。
2. 在 Zenodo 打开 GitHub integration。
3. 启用 `trustfedfusion-ids` 仓库。
4. 在 GitHub 创建 release，例如 `v0.1-release-candidate`。
5. Zenodo 会为该 release 生成 DOI。

如果直接手动上传 Zenodo:

1. 上传 `08_Submission/trustfedfusion-ids-release-candidate-v0.1.zip`。
2. 软件记录可参考本目录 `.zenodo.json`。
3. 结果数据记录可参考 `08_Submission/zenodo_source_data_results_metadata_current.json`。

## 3. 生成真实 DOI 后

把真实 URL 和 DOI 填入:

```text
08_Submission/repository_identifier_intake_current.json
```

然后运行:

```text
PYTHONDONTWRITEBYTECODE=1 python3 08_Submission/scripts/validate_repository_identifier_intake.py
PYTHONDONTWRITEBYTECODE=1 python3 08_Submission/scripts/apply_repository_identifiers.py
PYTHONDONTWRITEBYTECODE=1 python3 06_Manuscript/scripts/generate_final_data_code_availability.py
PYTHONDONTWRITEBYTECODE=1 python3 08_Submission/scripts/rebuild_release_packages.py
PYTHONDONTWRITEBYTECODE=1 python3 08_Submission/scripts/validate_release_candidate.py
PYTHONDONTWRITEBYTECODE=1 python3 08_Submission/scripts/validate_deposit_metadata.py
PYTHONDONTWRITEBYTECODE=1 python3 09_Project_Management/scripts/run_full_project_gate_suite.py
```

只有当 `Identifier placeholder scan | PASS`、`Public deposit status | READY_FOR_DEPOSIT_CHECK`
和 `Deposit readiness | READY_FOR_DEPOSIT_CHECK` 都通过后，才把包当成最终公开 DOI 版本。

## 4. 不能上传的内容

- Kaggle / Colab token
- SSH 私钥
- 原始第三方大型数据集
- 未确认可再分发的完整处理后数据衍生文件
- 论文未定稿 no-abstract draft
- 出版商 PDF
