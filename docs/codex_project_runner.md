# Codex Project Runner

이 프로젝트는 프로젝트 로컬 래퍼 \`.codex-runner/run.sh\`로 Codex 자동 작업 루프를 실행할 수 있습니다.

## 파일 위치

- 로컬 manifest: \`.codex-runner/project.tsv\`
- 첫 실행 프롬프트: \`.codex-runner/initial.md\`
- 연속 실행 프롬프트: \`.codex-runner/resume.md\`
- 로컬 실행 래퍼: \`.codex-runner/run.sh\`

## 기본 명령

\`\`\`bash
./.codex-runner/run.sh run
\`\`\`

현재 프로젝트를 첫 스레드로 1회 실행합니다.

\`\`\`bash
./.codex-runner/run.sh loop 3
\`\`\`

현재 프로젝트를 3라운드 연속으로 실행합니다.
1라운드는 초기 프롬프트를 사용하고, 2라운드부터는 같은 thread를 이어서 개선합니다.

\`\`\`bash
./.codex-runner/run.sh continue latest
\`\`\`

가장 최근 실행을 같은 thread들로 한 번 더 이어서 실행합니다.

\`\`\`bash
./.codex-runner/run.sh status latest
./.codex-runner/run.sh tail latest
\`\`\`

상태표와 이벤트 로그를 확인합니다.

## 권장 운영 방식

1. \`.codex-runner/initial.md\`에 이 프로젝트에서 먼저 보게 할 문맥과 금지사항을 적습니다.
2. \`./.codex-runner/run.sh loop 2\` 또는 \`loop 3\`으로 짧은 자동 실행을 돌립니다.
3. 결과를 보고 필요하면 \`.codex-runner/resume.md\`를 조정한 뒤 다시 \`continue\` 또는 \`loop\`를 실행합니다.
4. 큰 변경을 허용할 때만 \`--dangerous\` 옵션을 사용합니다.

## 이 프로젝트에서 프롬프트를 조정할 때 권장하는 내용

- 반드시 읽어야 할 문서나 디렉터리
- 우선순위가 높은 개선 영역
- 건드리면 안 되는 파일이나 정책
- 최소 검증 기준
- 마지막 응답 형식

## 현재 프로젝트 안전선

이 프로젝트의 자동 runner는 일반 리팩터링 도구가 아니라, 본 프로젝트의 핵심 역할인 2차 검증 체계를 실행하고 강화하는 용도로 사용합니다.

반드시 지킬 경계:

- 1차 시트는 외부 자동화 증분 체계의 결과물입니다.
- 2차 시트는 최종 서버 배포 전 추가 품질 검증 결과물입니다.
- 1차 시트, 운영 JSON, CSS/UI는 임의로 덮어쓰지 않습니다.
- 모델 재처리 결과는 바로 운영 반영하지 않고, 검증/gate 산출물로만 다룹니다.
- apply성 작업은 명시 플래그와 결과 리포트가 있을 때만 수행합니다.

우선 읽을 문서:

- [stage2_validation_workflow.md](/Users/junheelee/Desktop/career_dashboard/docs/stage2_validation_workflow.md)
- [stage2_validation_latest.md](/Users/junheelee/Desktop/career_dashboard/docs/stage2_validation_latest.md)
- [incremental_automation_hardening_plan.md](/Users/junheelee/Desktop/career_dashboard/docs/incremental_automation_hardening_plan.md)
- [source_count_incident_2026-04-12.md](/Users/junheelee/Desktop/career_dashboard/docs/source_count_incident_2026-04-12.md)

권장 작업:

- `scripts/run_stage2_validation.py`의 품질 검증 규칙 강화
- `scripts/run_stage2_deploy_gate.py`의 fail-closed 배포 차단 기준 강화
- 1차와 2차 결과의 diff/stale/approval gate 개선
- `data/stage2_validation_latest.json`과 `docs/stage2_validation_latest.md` 기반 리포트 개선
- 배포 전 gate가 실패할 때 운영 반영을 차단하는 fail-closed 체계 개선

## 참고

전역 실행기 본체는 \`codex-project-runner\`이며, 여러 프로젝트를 한 번에 돌릴 때는 전역 manifest 방식도 그대로 사용할 수 있습니다.
