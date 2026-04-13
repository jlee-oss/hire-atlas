# Stage2 Deploy Gate Latest

- generatedAt: `2026-04-12T10:14:32.671745+00:00`
- status: `passed`
- passed: `True`

## Metrics

- `stage1Rows`: `187`
- `stage2Rows`: `187`
- `candidateRows`: `187`
- `approvedRows`: `187`
- `deployableRows`: `187`
- `pendingRows`: `0`
- `needsReviewRows`: `0`
- `highOrMediumPriorityRows`: `0`
- `blockingStateRows`: `0`
- `blockingIssueCount`: `0`
- `issueCountTotal`: `122`

## Criteria

- `stage2Readable` actual `True` target `True` passed `True`
- `rowCountAligned` actual `{'stage1': 187, 'stage2': 187, 'candidates': 187}` target `stage1 == stage2 == candidates > 0` passed `True`
- `noRemovedFromStage1` actual `0` target `0` passed `True`
- `noBlockingStates` actual `0` target `0` passed `True`
- `noBlockingIssueCounts` actual `0` target `0` passed `True`
- `noPendingRows` actual `0` target `0` passed `True`
- `noNeedsReviewRows` actual `0` target `0` passed `True`
- `allRowsApproved` actual `187` target `187` passed `True`
- `deployRowsMatchStage1` actual `187` target `187` passed `True`

## Blocking Issue Counts


## Severity Counts

- `info`: `119`
- `low`: `3`

## Examples

### pending

- none

### needsReview

- none

### unapproved

- none

### blocking

- none

## Outputs

- gateJson: `/Users/junheelee/Desktop/career_dashboard/data/stage2_deploy_gate_latest.json`
- gateMd: `/Users/junheelee/Desktop/career_dashboard/docs/stage2_deploy_gate_latest.md`
- deployCsv: `/Users/junheelee/Desktop/career_dashboard/data/stage2_deploy_candidates_latest.csv`
