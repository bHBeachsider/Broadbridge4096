# Broadbridge AWS starter

Run these reference scripts on the AWS GPU host after provisioning the resources in AWS 2 of the implementation runbook. Do not run them in local Windows PowerShell.

1. Extract this ZIP under /srv/broadbridge and activate the selected DLAMI PyTorch environment.
2. Run bash bootstrap.sh and source /srv/broadbridge/venv/bin/activate.
3. Run python foundation_download.py --resolve-only. Review and retain the exact revision and upstream license.
4. Run python foundation_download.py --revision FULL_40_CHARACTER_SHA.
5. Use the runbook S3 sync command to archive the snapshot with the real bucket and KMS key.
6. Run python foundation_smoke.py --model LOCAL_SNAPSHOT_PATH --image fixtures/demo_pressure.png --output /srv/broadbridge/runs/baseline/baseline_smoke.json.

These files were syntax checked locally. They have not been executed against AWS, a GPU, or downloaded model weights. The bootstrap selects candidate library versions; freeze the exact working environment only after the inference and train/save/reload checks pass. S3 IAM/KMS permissions and model licenses must already be configured. No credentials belong in this ZIP.

The synthetic chart is a format fixture. Passing the smoke check does not establish engineering competence. Use the companion training-format kit for the later adapter smoke test, then process cleared source files and reviewed examples according to the implementation workbook.
