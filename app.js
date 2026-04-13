const STORAGE_KEY = "summary_table_llm_config";
const DEFAULT_BASE_URL = "http://127.0.0.1:11434/v1";
const DEFAULT_MODEL = "qwen2.5:7b";
const CLUSTER_TONES = [
  "cluster-a",
  "cluster-b",
  "cluster-c",
  "cluster-d",
  "cluster-e",
  "cluster-f",
  "cluster-g",
];

const SECTION_THEMES = [
  {
    id: "edge",
    tone: "cluster-a",
    label: "추론 최적화 · 컴퓨팅",
    description: "온디바이스 추론과 시스템 최적화 신호가 강한 묶음",
    tokens: ["엔피유", "npu", "onnx", "포팅", "컴파일러", "컴퓨팅", "최적화", "배포", "임베디드"],
  },
  {
    id: "health",
    tone: "cluster-b",
    label: "헬스케어 · 진단 지원",
    description: "의료 해석과 진단 지원 문장이 반복되는 묶음",
    tokens: ["헬스케어", "의료", "환자", "진단", "진료", "모니터링", "병원", "의료기기", "영상"],
  },
  {
    id: "data",
    tone: "cluster-c",
    label: "데이터 분석 · 실험 운영",
    description: "지표 분석과 실험 설계 신호가 많은 묶음",
    tokens: ["데이터분석", "데이터", "실험", "지표", "통계", "예측", "마트", "etl", "crm", "분석"],
  },
  {
    id: "industrial",
    tone: "cluster-d",
    label: "산업 현장 · 설계 자동화",
    description: "제조·설계·현장 자동화 문장이 드러나는 묶음",
    tokens: ["cad", "제조", "산업", "현장", "설계", "로봇", "공장", "시뮬레이션", "검증"],
  },
  {
    id: "service",
    tone: "cluster-e",
    label: "AI 제품화 · 서비스 적용",
    description: "언어·추천·검색 기반 서비스 적용 신호가 반복되는 묶음",
    tokens: ["llm", "rag", "추천", "검색", "에이전트", "멀티모달", "서비스", "제품", "교육", "금융"],
  },
  {
    id: "enterprise",
    tone: "cluster-f",
    label: "기업 업무 · 솔루션 구축",
    description: "고객사 환경과 솔루션 구축 문장이 많은 묶음",
    tokens: ["고객", "고객사", "솔루션", "엔터프라이즈", "업무", "플랫폼", "자동화", "구축"],
  },
  {
    id: "other",
    tone: "cluster-g",
    label: "기타 패턴",
    description: "명확한 하나의 테마로 수렴되기 전 단계의 묶음",
    tokens: [],
  },
];

const FIELD_SECTIONS = [
  {
    id: "detailBody",
    label: "상세본문",
    copy: "",
    modeLabel: "본문 그룹",
    maxClusters: 6,
    values: (row) => [row.detailBody || ""],
  },
  {
    id: "tasks",
    label: "주요업무",
    copy: "",
    modeLabel: "업무 그룹",
    maxClusters: 4,
    values: (row) => row.tasks || [],
  },
  {
    id: "requirements",
    label: "자격요건",
    copy: "",
    modeLabel: "자격 그룹",
    maxClusters: 4,
    values: (row) => row.requirements || [],
  },
  {
    id: "preferred",
    label: "우대사항",
    copy: "",
    modeLabel: "우대 그룹",
    maxClusters: 4,
    values: (row) => row.preferred || [],
  },
  {
    id: "skills",
    label: "핵심기술",
    copy: "",
    modeLabel: "기술 그룹",
    maxClusters: 4,
    values: (row) => row.skills || [],
  },
];

const SEMANTIC_BUNDLE_SECTION = {
  id: "semanticBundles",
  label: "분야별 채용 트렌드",
  modeLabel: "의미 조합",
};

const STOPWORDS = new Set([
  "ai",
  "인공지능",
  "엔지니어",
  "리서처",
  "개발",
  "개발자",
  "연구",
  "분석",
  "데이터",
  "모델",
  "업무",
  "경력",
  "신입",
  "우대",
  "자격",
  "요건",
  "주요",
  "핵심",
  "기술",
  "필수",
  "가능",
  "경험",
  "능력",
  "이해",
  "관련",
  "수행",
  "활용",
  "위한",
  "또는",
  "기반",
  "대한",
  "통한",
  "중심",
  "제품",
  "서비스",
  "학력",
  "학위",
  "학사",
  "석사",
  "박사",
  "전공",
  "신입",
  "필수",
  "우대",
  "요건",
  "자격",
  "가능",
  "이상",
  "보유",
  "분야",
  "관련분야",
  "모집",
  "채용",
  "인재채용",
  "모집요강",
  "상시채용",
  "경력무관",
  "계약직",
  "정규직",
  "근무지",
  "모집기간",
  "모집인원",
  "지원하기",
  "기획자",
  "담당자",
  "광주지사",
  "과천",
]);

const FIELD_STOPWORDS = new Set([
  ...STOPWORDS,
  "직무",
  "포지션",
  "이상",
  "보유",
  "우수",
  "관련분야",
  "유관분야",
  "업계",
  "전공",
  "분야",
  "기반",
  "중심",
  "역량",
  "조건",
  "요소",
  "문장",
  "환경",
  "문제해결",
  "커뮤니케이션",
  "협업",
  "경험이",
  "경력이",
  "있는",
  "있으신",
  "있으면",
  "좋습니다",
  "합니다",
  "우대합니다",
  "필요합니다",
  "이해가",
  "능력이",
  "역량을",
  "분을",
  "준하는",
  "보유하신",
  "활용한",
  "개발합니다",
  "구축합니다",
  "구현합니다",
  "설계하고",
  "수행합니다",
  "파이프라인을",
  "데이터를",
  "모델을",
  "시스템을",
]);

const TERM_ALIASES = [
  { label: "멀티모달", patterns: ["멀티모달", "multimodal"] },
  { label: "LLM", patterns: ["llm", "엘엘엠", "거대언어모델"] },
  { label: "RAG", patterns: ["rag", "검색증강생성", "retrievalaugmentedgeneration"] },
  { label: "컴퓨터비전", patterns: ["컴퓨터비전", "computervision", "영상처리"] },
  { label: "NLP", patterns: ["nlp", "자연어처리"] },
  { label: "MLOps", patterns: ["mlops"] },
  { label: "LLMOps", patterns: ["llmops"] },
  { label: "지식그래프", patterns: ["지식그래프", "knowledgegraph"] },
  { label: "GNN", patterns: ["gnn", "그래프신경망"] },
  { label: "추천 시스템", patterns: ["추천시스템", "추천 시스템", "추천"] },
  { label: "검색 시스템", patterns: ["검색시스템", "검색 시스템", "검색"] },
  { label: "데이터 파이프라인", patterns: ["데이터파이프라인", "데이터 파이프라인", "etl", "파이프라인"] },
  { label: "실험 설계", patterns: ["실험설계", "실험 설계", "ab테스트", "a/b테스트", "ab test", "a/b test"] },
  { label: "통계 분석", patterns: ["통계분석", "통계 분석", "지표분석", "데이터분석"] },
  { label: "모델 서빙", patterns: ["모델서빙", "모델 서빙", "서빙"] },
  { label: "온디바이스", patterns: ["온디바이스", "ondevice", "edgeai", "edge ai"] },
  { label: "임베디드", patterns: ["임베디드", "embedded"] },
  { label: "시뮬레이션", patterns: ["시뮬레이션", "simulation"] },
  { label: "테스트벤치", patterns: ["테스트벤치", "testbench"] },
  { label: "헬스케어", patterns: ["헬스케어", "의료", "의료기기"] },
  { label: "의료영상", patterns: ["의료영상", "medical imaging"] },
  { label: "금융", patterns: ["금융", "핀테크"] },
  { label: "교육", patterns: ["교육", "에듀테크"] },
  { label: "제조", patterns: ["제조", "스마트팩토리"] },
  { label: "로보틱스", patterns: ["로봇", "로보틱스"] },
  { label: "API", patterns: ["api"] },
  { label: "도커", patterns: ["docker", "도커"] },
  { label: "쿠버네티스", patterns: ["kubernetes", "쿠버네티스", "k8s"] },
  { label: "AWS", patterns: ["aws", "에이더블유에스"] },
  { label: "GCP", patterns: ["gcp", "지씨피", "gcs"] },
  { label: "SQL", patterns: ["sql", "에스큐엘"] },
  { label: "Python", patterns: ["python", "파이썬"] },
  { label: "PyTorch", patterns: ["pytorch", "파이토치"] },
  { label: "TensorFlow", patterns: ["tensorflow", "텐서플로"] },
  { label: "전문연구요원", patterns: ["전문연구요원", "병역특례"] },
];

const ALLOWED_SHORT_TERM_KEYS = new Set(
  ["llm", "rag", "nlp", "sql", "etl", "crm", "api", "sdk", "aws", "gcp", "npu", "cad", "bi"].map(canonical),
);

const WEAK_FIELD_TERM_KEYS = new Set(
  [
    "위한",
    "또는",
    "기반",
    "대한",
    "관련",
    "통한",
    "중심",
    "있는",
    "있으신",
    "있으면",
    "가능",
    "가능한",
    "필요",
    "필수",
    "우대",
    "요건",
    "자격",
    "학력",
    "학위",
    "학사",
    "석사",
    "박사",
    "전공",
    "경력",
    "신입",
    "보유",
    "분야",
    "제품",
    "서비스",
    "시스템",
    "프로젝트",
    "다양한",
    "있어야",
    "보유해야",
    "미기재",
    "우대사항",
    "컴퓨터",
    "컴퓨터공학",
    "비즈니스",
    "소프트웨어",
    "프레임워크",
    "글로벌",
    "사용자",
    "고객사",
    "솔루션",
    "대규모",
    "복잡한",
    "서류접수",
    "면접",
    "차면접",
    "모집",
    "채용",
    "인재채용",
    "모집요강",
    "상시채용",
    "경력무관",
    "계약직",
    "정규직",
    "근무지",
    "모집기간",
    "모집인원",
    "지원하기",
    "기획자",
    "담당자",
    "광주지사",
    "과천",
    "개발",
    "분석",
    "설계",
    "운영",
    "구축",
    "모델",
    "데이터",
    "기술",
  ].map(canonical),
);

const NON_SKILL_GENERIC_KEYS = new Set(
  ["python", "파이썬", "sql", "aws", "gcp", "docker", "도커"].map(canonical),
);

const BROAD_CLUSTER_LABEL_KEYS = new Set(
  [
    "통계분석",
    "데이터분석",
    "인프라",
    "클라우드",
    "api",
    "대시보드",
    "검증",
    "실험설계",
    "자동화",
  ].map(canonical),
);

const TERM_ENDING_PATTERNS = [
  /(합니다|합니다만|좋습니다|우대합니다|필요합니다|개발합니다|구축합니다|구현합니다|수행합니다|설계하고)$/u,
  /(경험이|경력이|이상의|이상|준하는|보유하신|보유해야|분을|능력이|이해가|역량을|있어야)$/u,
  /(위한|또는|관련|대한|통한|기반|중심|가능한|가능)$/u,
  /(하고|하며|하여|하는|하신|여야|으신|필요한|없으신)$/u,
];

const state = {
  board: null,
  roleFilter: "전체",
  activityFilter: "active",
  clusterMap: new Map(),
  activeClusterKey: null,
  drawerClusterKey: null,
  drawerCloseTimer: 0,
  drawerIsClosing: false,
  companyHoverTarget: null,
  companyHoverTimer: 0,
  companyHoverRequestId: 0,
  companyInsightCache: new Map(),
  roleResumeOpen: false,
  roleResumeLoading: false,
  roleResumeError: "",
  roleResumeGuides: null,
  roleResumeRole: "",
  roleResumeActivityMode: "all",
  roleResumeRequestId: 0,
  roleResumeLoadingMode: "open",
  roleResumeLoadingStepIndex: 0,
  roleResumeNotice: "",
  roleResumeNoticeTone: "neutral",
  roleResumeStreamLog: [],
  roleResumeStreamPreview: "",
  roleResumePdfExporting: false,
};

const ROLE_ICON_META = {
  전체: { icon: "icon-all", badge: "All" },
  "인공지능 엔지니어": { icon: "icon-engineer", badge: "AI Engineer" },
  "인공지능 리서처": { icon: "icon-researcher", badge: "AI Researcher" },
  "데이터 사이언티스트": { icon: "icon-scientist", badge: "Data Scientist" },
  "데이터 분석가": { icon: "icon-analyst", badge: "Data Analyst" },
};

const elements = {
  siteIntro: document.querySelector("#site-intro"),
  baseUrl: document.querySelector("#base-url"),
  modelName: document.querySelector("#model-name"),
  apiKey: document.querySelector("#api-key"),
  batchSize: document.querySelector("#batch-size"),
  saveConfig: document.querySelector("#save-config"),
  openRoleResumeGuides: document.querySelector("#open-role-resume-guides"),
  roleResumeSlot: document.querySelector("#role-resume-slot"),
  syncSheet: document.querySelector("#sync-sheet"),
  runMissing: document.querySelector("#run-missing"),
  runAll: document.querySelector("#run-all"),
  refreshBoard: document.querySelector("#refresh-board"),
  roleTabs: document.querySelector("#role-tabs"),
  activityTabs: document.querySelector("#activity-tabs"),
  semanticBundles: document.querySelector("#semantic-bundles"),
  fieldSections: document.querySelector("#field-sections"),
  overviewText: document.querySelector("#overview-text"),
  statusText: document.querySelector("#status-text"),
  clusterDrawerShell: document.querySelector("#cluster-drawer-shell"),
  clusterDrawerScrim: document.querySelector("#cluster-drawer-scrim"),
  clusterDrawerPanel: document.querySelector("#cluster-drawer-panel"),
  clusterDrawerContent: document.querySelector("#cluster-drawer-content"),
  roleResumeShell: document.querySelector("#role-resume-shell"),
  roleResumeScrim: document.querySelector("#role-resume-scrim"),
  roleResumePanel: document.querySelector("#role-resume-panel"),
  roleResumeContent: document.querySelector("#role-resume-content"),
  companyHoverPopover: document.querySelector("#company-hover-popover"),
  companyHoverLabel: document.querySelector("#company-hover-label"),
  companyHoverBody: document.querySelector("#company-hover-body"),
  companyHoverHeadline: document.querySelector("#company-hover-headline"),
  companyHoverParagraphs: document.querySelector("#company-hover-paragraphs"),
  companyHoverSignals: document.querySelector("#company-hover-signals"),
  companyHoverLoading: document.querySelector("#company-hover-loading"),
  companyHoverLoadingCopy: document.querySelector("#company-hover-loading-copy"),
};

const ROLE_RESUME_LOADING_STEPS = {
  open: [
    "저장된 결과가 있는지 확인하고 있습니다.",
    "직무별 채용 신호를 다시 읽고 있습니다.",
    "문서 구조를 정리하고 있습니다.",
    "문장을 다듬고 있습니다.",
  ],
  regenerate: [
    "캐시를 건너뛰고 새 추론을 요청하고 있습니다.",
    "직무별 채용 신호를 다시 읽고 있습니다.",
    "프로젝트와 역량 축을 다시 배치하고 있습니다.",
    "문장을 다시 정리하고 있습니다.",
  ],
};

const introStartedAt = performance.now();
let introFinishTimer = 0;
let introCleanupTimer = 0;
let introFailsafeTimer = 0;
let roleResumeLoadingStepTimer = 0;
let roleResumeAbortController = null;

if (elements.siteIntro) {
  introFailsafeTimer = window.setTimeout(() => {
    finishSiteIntro(true);
  }, 3200);
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderAnimatedMetricText(value, extraClass = "") {
  return Array.from(String(value || ""))
    .map((char, index) => {
      const display = char === " " ? "&nbsp;" : escapeHtml(char);
      return `<span class="metric-char ${extraClass}" style="--char-delay:${index}">${display}</span>`;
    })
    .join("");
}

function buildClusterKey(sectionId, clusterId) {
  return `${sectionId}::${clusterId}`;
}

function escapeRegExp(value) {
  return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function canonical(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^0-9a-z가-힣]+/g, "");
}

function titleCaseToken(value) {
  const token = String(value || "").trim();
  if (!token) return "";
  if (/^[a-z0-9+./#-]+$/i.test(token)) {
    if (token.length <= 4 || /[+/#]/.test(token)) {
      return token.toUpperCase();
    }
    return token.charAt(0).toUpperCase() + token.slice(1).toLowerCase();
  }
  return token;
}

function normalizeTermLabel(value) {
  const raw = String(value || "").trim();
  const compact = canonical(raw);
  if (!compact) return "";

  for (const alias of TERM_ALIASES) {
    if (alias.patterns.some((pattern) => compact.includes(canonical(pattern)))) {
      return alias.label;
    }
  }

  return titleCaseToken(raw);
}

function uniqueTerms(values, limit = Infinity) {
  const seen = new Set();
  const output = [];
  (values || []).forEach((value) => {
    const label = normalizeTermLabel(value);
    const key = canonical(label);
    if (!key || seen.has(key)) return;
    seen.add(key);
    output.push(label);
  });
  return output.slice(0, limit);
}

function firstFilledList(...lists) {
  for (const list of lists) {
    if (Array.isArray(list) && list.length) {
      return list;
    }
  }
  return [];
}

function normalizeStructuredSignalsPayload(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const list = (key) => uniqueTerms(Array.isArray(source[key]) ? source[key] : [], 8);

  return {
    quality: String(source.quality || "").trim().toLowerCase(),
    domainSignals: list("domainSignals"),
    problemSignals: list("problemSignals"),
    systemSignals: list("systemSignals"),
    modelSignals: list("modelSignals"),
    dataSignals: list("dataSignals"),
    workflowSignals: list("workflowSignals"),
    roleSignals: list("roleSignals"),
    confidenceNotes: list("confidenceNotes"),
  };
}

function normalizeSignalFacetsPayload(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const list = (key) => uniqueTerms(Array.isArray(source[key]) ? source[key] : [], 8);

  return {
    role: list("role"),
    keyword: list("keyword"),
    tag: list("tag"),
    context: list("context"),
  };
}

function normalizeSectionSignalFacetsPayload(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const sections = ["detailBody", "tasks", "requirements", "preferred", "skills"];
  return Object.fromEntries(
    sections.map((sectionId) => [sectionId, normalizeSignalFacetsPayload(source[sectionId])]),
  );
}

function fallbackFocusLabel(row) {
  const facets = normalizeSignalFacetsPayload(row.signalFacets);
  const signals = normalizeStructuredSignalsPayload(row.structuredSignals);
  return (
    facets.keyword[0]
    || signals.problemSignals[0]
    || signals.domainSignals[0]
    || signals.dataSignals[0]
    || signals.systemSignals[0]
    || ""
  );
}

function fallbackHighlightKeywords(row) {
  const facets = normalizeSignalFacetsPayload(row.signalFacets);
  const signals = normalizeStructuredSignalsPayload(row.structuredSignals);
  return uniqueTerms(
    [
      ...(row.highlightKeywords || []),
      ...facets.keyword,
      ...signals.problemSignals,
      ...signals.dataSignals,
      ...signals.modelSignals,
      ...signals.systemSignals,
    ],
    6,
  );
}

function normalizeBoardPayload(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const rows = Array.isArray(source.rows) ? source.rows : [];
  const clusters = Array.isArray(source.clusters) ? source.clusters : [];
  const semanticBundles = Array.isArray(source.semanticBundles) ? source.semanticBundles : [];
  const semanticBundlesByRole =
    source.semanticBundlesByRole && typeof source.semanticBundlesByRole === "object"
      ? source.semanticBundlesByRole
      : {};
  const normalizeSemanticBundle = (bundle) => ({
    ...bundle,
    axes: uniqueTerms(bundle.axes || [], 6),
    skills: uniqueTerms(bundle.skills || [], 6),
    evidenceTerms: uniqueTerms(bundle.evidenceTerms || [], 8),
    sampleCompanies: uniqueTerms(bundle.sampleCompanies || [], 4),
    samplePostings: Array.isArray(bundle.samplePostings) ? bundle.samplePostings : [],
    postingIds: Array.isArray(bundle.postingIds) ? bundle.postingIds : [],
    postingCount: Number(bundle.postingCount) || 0,
    activePostingCount: Number(bundle.activePostingCount) || 0,
    companyCount: Number(bundle.companyCount) || 0,
    confidence: Number(bundle.confidence) || 0,
  });

  return {
    ...source,
    clusters: clusters.map((cluster) => ({
      ...cluster,
      keywords: uniqueTerms(firstFilledList(cluster.keywords, cluster.signalFacets?.keyword), 6),
      signalFacets: normalizeSignalFacetsPayload(cluster.signalFacets),
    })),
    rows: rows.map((row) => {
      const structuredSignals = normalizeStructuredSignalsPayload(row.structuredSignals);
      const signalFacets = normalizeSignalFacetsPayload(row.signalFacets);
      const highlightKeywords = fallbackHighlightKeywords({
        ...row,
        structuredSignals,
        signalFacets,
      });

      return {
        ...row,
        active: Boolean(row.active),
        tasks: Array.isArray(row.tasks) ? row.tasks : [],
        requirements: Array.isArray(row.requirements) ? row.requirements : [],
        preferred: Array.isArray(row.preferred) ? row.preferred : [],
        skills: Array.isArray(row.skills) ? row.skills : [],
        previewLines: Array.isArray(row.previewLines) ? row.previewLines : [],
        structuredSignals,
        signalFacets,
        sectionSignalFacets: normalizeSectionSignalFacetsPayload(row.sectionSignalFacets),
        clusterSignalFacets: normalizeSignalFacetsPayload(row.clusterSignalFacets),
        focusLabel: row.focusLabel || fallbackFocusLabel({ ...row, structuredSignals, signalFacets }),
        highlightKeywords,
        companyKeywords: uniqueTerms(
          firstFilledList(row.companyKeywords, row.clusterKeywords, signalFacets.tag),
          6,
        ),
      };
    }),
    semanticBundles: semanticBundles
      .map(normalizeSemanticBundle)
      .filter((bundle) => bundle.label && bundle.postingIds.length),
    semanticBundlesByRole: Object.fromEntries(
      Object.entries(semanticBundlesByRole).map(([role, bundles]) => [
        role,
        (Array.isArray(bundles) ? bundles : [])
          .map(normalizeSemanticBundle)
          .filter((bundle) => bundle.label && bundle.postingIds.length),
      ]),
    ),
  };
}

const ROLE_RESUME_SIGNAL_LABELS = {
  problemSignals: "핵심 과업",
  domainSignals: "도메인 맥락",
  systemSignals: "시스템 환경",
  modelSignals: "모델 축",
  dataSignals: "데이터 축",
  workflowSignals: "운영 흐름",
};

function normalizeCountList(values) {
  return (Array.isArray(values) ? values : [])
    .map((item) => ({
      label: String(item?.label || "").trim(),
      count: Number(item?.count) || 0,
    }))
    .filter((item) => item.label);
}

function normalizeRoleResumeResponse(payload) {
  const source = payload && typeof payload === "object" ? payload : {};
  const content = source.payload && typeof source.payload === "object" ? source.payload : {};
  const marketProfile = source.marketProfile && typeof source.marketProfile === "object"
    ? source.marketProfile
    : {};
  const structuredSignalCounts = marketProfile.structuredSignalCounts && typeof marketProfile.structuredSignalCounts === "object"
    ? marketProfile.structuredSignalCounts
    : {};

  return {
    role: String(source.role || marketProfile.role || "").trim(),
    activityFilter: String(source.activityFilter || marketProfile.activityFilter || "all").trim() || "all",
    cached: Boolean(source.cached),
    stale: Boolean(source.stale),
    provider: source.provider && typeof source.provider === "object" ? source.provider : {},
    marketProfile: {
      ...marketProfile,
      focusCounts: normalizeCountList(marketProfile.focusCounts),
      keywordCounts: normalizeCountList(marketProfile.keywordCounts),
      skillCounts: normalizeCountList(marketProfile.skillCounts),
      companyCounts: normalizeCountList(marketProfile.companyCounts),
      taskEvidence: normalizeCountList(marketProfile.taskEvidence),
      requirementEvidence: normalizeCountList(marketProfile.requirementEvidence),
      preferredEvidence: normalizeCountList(marketProfile.preferredEvidence),
      structuredSignalCounts: Object.fromEntries(
        Object.entries(structuredSignalCounts).map(([key, value]) => [key, normalizeCountList(value)]),
      ),
      postingSamples: (Array.isArray(marketProfile.postingSamples) ? marketProfile.postingSamples : [])
        .map((item) => ({
          company: String(item?.company || "").trim(),
          title: String(item?.title || "").trim(),
          focusLabel: String(item?.focusLabel || "").trim(),
          summary: String(item?.summary || "").trim(),
          keywords: uniqueTerms(Array.isArray(item?.keywords) ? item.keywords : [], 5),
          problemSignals: uniqueTerms(Array.isArray(item?.problemSignals) ? item.problemSignals : [], 3),
          systemSignals: uniqueTerms(Array.isArray(item?.systemSignals) ? item.systemSignals : [], 3),
          workflowSignals: uniqueTerms(Array.isArray(item?.workflowSignals) ? item.workflowSignals : [], 3),
        }))
        .filter((item) => item.title || item.summary),
    },
    payload: {
      panelTitle: String(content.panelTitle || "").trim(),
      panelSubtitle: String(content.panelSubtitle || "").trim(),
      marketReality: String(content.marketReality || "").trim(),
      honestyMessage: String(content.honestyMessage || "").trim(),
      document: {
        badge: String(content.document?.badge || "").trim(),
        headline: String(content.document?.headline || "").trim(),
        subheadline: String(content.document?.subheadline || "").trim(),
        summary: String(content.document?.summary || "").trim(),
        projects: (Array.isArray(content.document?.projects) ? content.document.projects : [])
          .map((project, projectIndex) => ({
            title: String(project?.title || `프로젝트 ${projectIndex + 1}`).trim(),
            meta: String(project?.meta || "").trim(),
            overview: String(project?.overview || "").trim(),
            responsibilities: (Array.isArray(project?.responsibilities) ? project.responsibilities : [])
              .map((item) => String(item || "").trim())
              .filter(Boolean),
            achievements: (Array.isArray(project?.achievements) ? project.achievements : [])
              .map((item) => String(item || "").trim())
              .filter(Boolean),
          }))
          .filter((project) => project.title),
        education: (Array.isArray(content.document?.education) ? content.document.education : [])
          .map((item) => ({
            title: String(item?.title || "").trim(),
            meta: String(item?.meta || "").trim(),
          }))
          .filter((item) => item.title || item.meta),
        skills: uniqueTerms(Array.isArray(content.document?.skills) ? content.document.skills : [], 12),
        portfolio: (Array.isArray(content.document?.portfolio) ? content.document.portfolio : [])
          .map((item) => String(item || "").trim())
          .filter(Boolean),
        footerNote: String(content.document?.footerNote || "").trim(),
      },
    },
  };
}

function buildRoleResumePdfFilename(roleLabel, documentData) {
  const raw = [roleLabel, documentData?.headline || "ai-resume"]
    .map((value) =>
      String(value || "")
        .trim()
        .replace(/[\\/:*?"<>|]+/g, " ")
        .replace(/\s+/g, "-"),
    )
    .filter(Boolean)
    .join("_");
  return `${raw || "ai_resume"}_${new Date().toISOString().slice(0, 10)}.pdf`;
}

function parseDownloadFilename(disposition) {
  const value = String(disposition || "");
  const utf8Match = value.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match) {
    try {
      return decodeURIComponent(utf8Match[1]);
    } catch (error) {
      return utf8Match[1];
    }
  }
  const plainMatch = value.match(/filename="([^"]+)"/i) || value.match(/filename=([^;]+)/i);
  return plainMatch ? plainMatch[1].trim() : "";
}

async function downloadRoleResumePdf() {
  if (state.roleResumePdfExporting) return;
  const documentData = state.roleResumeGuides?.payload?.document;
  if (!documentData) {
    setStatus("PDF로 저장할 문서가 아직 없습니다.");
    return;
  }

  state.roleResumePdfExporting = true;
  state.roleResumeNotice = "";
  state.roleResumeNoticeTone = "neutral";
  renderRoleResumeOverlay();
  await waitForNextPaint();
  setStatus("PDF 다운로드를 준비하는 중...");

  try {
    const response = await fetch("/api/role-resume-guides/pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role: state.roleResumeRole,
        payload: state.roleResumeGuides?.payload || {},
      }),
    });
    if (!response.ok) {
      let message = "PDF 다운로드에 실패했습니다.";
      try {
        const body = await response.json();
        message = body.error || message;
      } catch (error) {
        message = (await response.text()) || message;
      }
      throw new Error(message);
    }
    const blob = await response.blob();
    if (!blob.size) {
      throw new Error("비어 있는 PDF가 내려왔습니다.");
    }
    const disposition = response.headers.get("Content-Disposition");
    const filename = parseDownloadFilename(disposition) || buildRoleResumePdfFilename(state.roleResumeRole, documentData);
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
    setStatus("PDF 다운로드를 시작했습니다.");
  } catch (error) {
    state.roleResumeNotice = `PDF 저장에 실패했습니다. ${error.message}`;
    state.roleResumeNoticeTone = "error";
    setStatus(error.message);
  } finally {
    state.roleResumePdfExporting = false;
    renderRoleResumeOverlay();
  }
}

function readBatchSize() {
  return Math.max(1, Number.parseInt(elements.batchSize.value, 10) || 2);
}

function readConfig() {
  return {
    baseUrl: elements.baseUrl.value.trim(),
    model: elements.modelName.value.trim(),
    apiKey: elements.apiKey.value.trim(),
    batchSize: readBatchSize(),
  };
}

function isLocalModelBaseUrl(baseUrl) {
  return /^https?:\/\/(127\.0\.0\.1|localhost|\[::1\])(?::\d+)?(?:\/|$)/i.test(String(baseUrl || "").trim());
}

function hasUsableModelConfig(config) {
  const baseUrl = String(config?.baseUrl || "").trim();
  const model = String(config?.model || "").trim();
  return Boolean(baseUrl && model);
}

function readRoleResumeConfig() {
  const config = readConfig();
  const baseUrl = String(config.baseUrl || "").trim();
  const model = String(config.model || "").trim();
  const hasExplicitResumeProvider =
    (!!baseUrl && baseUrl !== DEFAULT_BASE_URL) || /gemma/i.test(model);

  if (!hasExplicitResumeProvider) {
    return null;
  }

  return {
    ...config,
    model: /gemma/i.test(model) ? model : "gemma-4-31b",
  };
}

function hasSavedModelProvider() {
  const saved = loadSavedConfig();
  return Boolean(String(saved.baseUrl || "").trim() && String(saved.model || "").trim());
}

function readCompanyInsightConfig() {
  const config = readConfig();
  return hasSavedModelProvider() && hasUsableModelConfig(config) ? config : null;
}

function hasLiveCompanyInsightConfig() {
  const config = readCompanyInsightConfig();
  return config ? hasUsableModelConfig(config) : true;
}

function hasLiveRoleResumeConfig() {
  const config = readRoleResumeConfig();
  return config ? hasUsableModelConfig(config) : true;
}

function writeConfig(config) {
  elements.baseUrl.value = config.baseUrl || DEFAULT_BASE_URL;
  elements.modelName.value = config.model || DEFAULT_MODEL;
  elements.apiKey.value = config.apiKey || "";
  elements.batchSize.value = String(Math.max(1, Number.parseInt(config.batchSize, 10) || 2));
}

function loadSavedConfig() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
  } catch (error) {
    return {};
  }
}

function saveConfig() {
  const config = readConfig();
  localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
  setStatus(`설정을 저장했습니다. ${config.baseUrl} / ${config.model}`);
  renderRoleResumeButton();
  return config;
}

function requireConfig() {
  const config = readConfig();
  if (!config.baseUrl || !config.model) {
    throw new Error("Base URL과 Model을 먼저 입력해주세요.");
  }
  return config;
}

function setStatus(message) {
  if (elements.statusText) {
    elements.statusText.textContent = message;
  }
}

function waitForNextPaint() {
  return new Promise((resolve) => {
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(resolve);
    });
  });
}

function abortRoleResumeRequest() {
  if (!roleResumeAbortController) return;
  roleResumeAbortController.abort();
  roleResumeAbortController = null;
}

function clearRoleResumeLoadingTicker() {
  if (!roleResumeLoadingStepTimer) return;
  window.clearInterval(roleResumeLoadingStepTimer);
  roleResumeLoadingStepTimer = 0;
}

function currentRoleResumeLoadingSteps() {
  return ROLE_RESUME_LOADING_STEPS[state.roleResumeLoadingMode] || ROLE_RESUME_LOADING_STEPS.open;
}

function syncRoleResumePhaseFromMessage(message) {
  const text = String(message || "");
  if (text.includes("시장 신호")) {
    state.roleResumeLoadingStepIndex = 0;
    return;
  }
  if (text.includes("연결")) {
    state.roleResumeLoadingStepIndex = 1;
    return;
  }
  if (text.includes("응답 스트림")) {
    state.roleResumeLoadingStepIndex = 2;
    return;
  }
  if (text.includes("실시간으로 문서를 작성")) {
    state.roleResumeLoadingStepIndex = 3;
    return;
  }
  if (text.includes("문서 형식으로 변환") || text.includes("스트림을 정리")) {
    state.roleResumeLoadingStepIndex = 4;
  }
}

function startRoleResumeLoadingTicker(mode = "open") {
  clearRoleResumeLoadingTicker();
  state.roleResumeLoadingMode = mode;
  state.roleResumeLoadingStepIndex = 0;
  roleResumeLoadingStepTimer = window.setInterval(() => {
    if (!state.roleResumeLoading) {
      clearRoleResumeLoadingTicker();
      return;
    }
    const steps = currentRoleResumeLoadingSteps();
    state.roleResumeLoadingStepIndex = Math.min(
      state.roleResumeLoadingStepIndex + 1,
      Math.max(steps.length - 1, 0),
    );
    renderRoleResumeOverlay();
  }, 900);
}

function renderRoleResumeLoadingSteps() {
  const steps = currentRoleResumeLoadingSteps();
  const progress = Math.max(14, Math.min(96, ((state.roleResumeLoadingStepIndex + 1) / steps.length) * 100));
  return `
    <div class="role-resume-stage-shell">
      <div class="role-resume-progress-meta">
        <span>현재 단계</span>
        <strong>${escapeHtml(steps[state.roleResumeLoadingStepIndex] || steps[0] || "생성 중")}</strong>
      </div>
      <div class="role-resume-loading-progress" aria-hidden="true">
        <span style="width:${progress}%"></span>
      </div>
    </div>
    <ol class="role-resume-loading-steps">
      ${steps
        .map((step, index) => {
          let className = "";
          if (index < state.roleResumeLoadingStepIndex) className = "is-done";
          else if (index === state.roleResumeLoadingStepIndex) className = "is-active";
          else className = "is-pending";
          return `
            <li class="${className}">
              <span class="role-resume-step-dot" aria-hidden="true"></span>
              <span class="role-resume-step-text">${escapeHtml(step)}</span>
            </li>
          `;
        })
        .join("")}
    </ol>
  `;
}

function resetRoleResumeStreamState() {
  state.roleResumeStreamLog = [];
  state.roleResumeStreamPreview = "";
}

function pushRoleResumeStreamLog(message) {
  const cleaned = String(message || "").trim();
  if (!cleaned) return;
  const previous = state.roleResumeStreamLog[state.roleResumeStreamLog.length - 1];
  if (previous === cleaned) return;
  state.roleResumeStreamLog = [...state.roleResumeStreamLog.slice(-7), cleaned];
}

function appendRoleResumeStreamPreview(chunk) {
  if (!chunk) return;
  state.roleResumeStreamPreview = `${state.roleResumeStreamPreview}${String(chunk)}`.slice(-2800);
}

function renderRoleResumeStreamLog() {
  const logs = state.roleResumeStreamLog.length ? state.roleResumeStreamLog : ["요청을 보내고 있습니다."];
  return `
    <ul class="role-resume-stream-log">
      ${logs.map((line) => `<li>${escapeHtml(line)}</li>`).join("")}
    </ul>
  `;
}

function renderRoleResumeStreamPreview() {
  if (!state.roleResumeStreamPreview.trim()) {
    return `<p class="role-resume-stream-placeholder">아직 모델 출력이 도착하지 않았습니다.</p>`;
  }
  return `<pre class="role-resume-stream-preview">${escapeHtml(state.roleResumeStreamPreview)}</pre>`;
}

function renderRoleResumeToolbar() {
  const downloadLabel = state.roleResumePdfExporting ? "PDF 준비 중..." : "PDF 다운로드";
  const canRegenerate = hasLiveRoleResumeConfig() && !state.roleResumePdfExporting;
  return `
    <div class="role-resume-toolbar">
      <div class="role-resume-toolbar-copy">
        ${
          state.roleResumeNotice
            ? `<p class="role-resume-toolbar-note ${state.roleResumeNoticeTone === "error" ? "is-error" : ""}">${escapeHtml(state.roleResumeNotice)}</p>`
            : ""
        }
      </div>
      <div class="role-resume-toolbar-actions">
        <button
          type="button"
          class="role-resume-action-button"
          data-download-role-resume-pdf
          ${state.roleResumePdfExporting ? 'disabled aria-disabled="true"' : ""}
        >
          ${downloadLabel}
        </button>
        <button
          type="button"
          class="role-resume-action-button"
          data-regenerate-role-resume
          ${canRegenerate ? "" : 'disabled aria-disabled="true" title="모델 설정을 저장하면 새 AI 문서를 만들 수 있습니다."'}
        >
          다시 만들기
        </button>
      </div>
    </div>
  `;
}

function parseSseEventBlock(block) {
  let event = "message";
  const dataLines = [];
  block.split(/\r?\n/).forEach((line) => {
    if (!line || line.startsWith(":")) return;
    if (line.startsWith("event:")) {
      event = line.slice(6).trim() || "message";
      return;
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  });
  const raw = dataLines.join("\n");
  if (!raw) return { event, payload: {} };
  try {
    return { event, payload: JSON.parse(raw) };
  } catch (error) {
    return { event, payload: { raw } };
  }
}

async function postEventStream(url, payload, { signal, onEvent } = {}) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    const text = await response.text();
    let body = null;
    try {
      body = JSON.parse(text);
    } catch (error) {
      body = null;
    }
    throw new Error(body?.error || text || "요청 실패");
  }

  if (!response.body) {
    throw new Error("스트림 응답을 받을 수 없습니다.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    while (true) {
      const boundary = buffer.search(/\r?\n\r?\n/);
      if (boundary === -1) break;
      const block = buffer.slice(0, boundary);
      const separator = buffer.slice(boundary).match(/^\r?\n\r?\n/);
      buffer = buffer.slice(boundary + (separator ? separator[0].length : 2));
      const parsed = parseSseEventBlock(block);
      onEvent?.(parsed.event, parsed.payload);
    }
  }

  const flushed = buffer + decoder.decode();
  if (flushed.trim()) {
    const parsed = parseSseEventBlock(flushed);
    onEvent?.(parsed.event, parsed.payload);
  }
}

function finishSiteIntro(force = false) {
  if (introFailsafeTimer) {
    window.clearTimeout(introFailsafeTimer);
    introFailsafeTimer = 0;
  }

  if (document.body.classList.contains("intro-complete")) {
    return;
  }

  if (introFinishTimer) {
    window.clearTimeout(introFinishTimer);
    introFinishTimer = 0;
  }
  if (introCleanupTimer) {
    window.clearTimeout(introCleanupTimer);
    introCleanupTimer = 0;
  }

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const minimumDuration = reduceMotion ? 220 : 1500;
  const exitDuration = reduceMotion ? 180 : 860;
  const elapsed = performance.now() - introStartedAt;
  const waitTime = force ? 0 : Math.max(0, minimumDuration - elapsed);

  introFinishTimer = window.setTimeout(() => {
    document.body.classList.add("intro-exit");
    introCleanupTimer = window.setTimeout(() => {
      document.body.classList.remove("intro-active", "intro-exit");
      document.body.classList.add("intro-complete");
      elements.siteIntro?.remove();
    }, exitDuration);
  }, waitTime);
}

function roleFilters() {
  const overviewFilters = state.board?.overview?.roleFilters;
  if (Array.isArray(overviewFilters) && overviewFilters.length) {
    return overviewFilters;
  }

  const counts = new Map();
  (state.board?.rows || []).forEach((row) => {
    const role = row.roleGroup || row.role;
    if (!role) return;
    counts.set(role, (counts.get(role) || 0) + 1);
  });

  const derived = Array.from(counts.entries())
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .map(([name, count]) => ({ name, count }));

  return [{ name: "전체", count: state.board?.rows?.length || 0 }, ...derived];
}

function currentRows() {
  const rows = state.board?.rows || [];
  let filtered = rows;

  if (state.roleFilter !== "전체") {
    filtered = filtered.filter((row) => row.roleGroup === state.roleFilter);
  }
  if (state.activityFilter === "active") {
    filtered = filtered.filter((row) => row.active);
  }
  return filtered;
}

function renderOverview() {
  if (!state.board || !elements.overviewText) return;

  const rows = currentRows();
  const roleLabel = state.roleFilter === "전체" ? "전체 직무" : state.roleFilter;
  const activityLabel = state.activityFilter === "active" ? "활성 공고만" : "전체 상태";

  if (!rows.length) {
    elements.overviewText.textContent = `${roleLabel} · ${activityLabel} · 결과 없음`;
    return;
  }

  const companyCount = new Set(rows.map((row) => row.company).filter(Boolean)).size;
  elements.overviewText.textContent =
    `${roleLabel} · ${activityLabel} · ${rows.length}개 공고 · ${companyCount}개 기업`;
}

function canOpenRoleResumeGuides() {
  return state.roleFilter !== "전체" && state.roleFilter !== "기타" && currentRows().length > 0;
}

function renderRoleResumeButton() {
  if (!elements.openRoleResumeGuides) return;
  const button = elements.openRoleResumeGuides;
  const slot = elements.roleResumeSlot;
  const canOpen = canOpenRoleResumeGuides();
  const isBusy = state.roleResumeLoading;
  const shouldShow = state.roleFilter !== "전체" && state.roleFilter !== "기타";
  const note = button.querySelector(".action-visual-note");
  const hasLiveAi = hasLiveRoleResumeConfig();

  if (slot) {
    slot.classList.toggle("is-active", shouldShow);
    slot.setAttribute("aria-hidden", shouldShow ? "false" : "true");
  }

  button.hidden = !shouldShow;
  if (!shouldShow) {
    button.disabled = true;
    button.setAttribute("aria-disabled", "true");
    button.classList.remove("is-loading");
    if (note) note.textContent = hasLiveAi ? "AI 문서 생성" : "저장 문서 열기";
    return;
  }

  button.disabled = !canOpen || isBusy;
  button.setAttribute("aria-disabled", String(!canOpen || isBusy));
  button.classList.toggle("is-loading", isBusy);

  if (note) {
    if (isBusy) {
      note.textContent = hasLiveAi ? "AI 생성 중" : "저장 문서 확인";
    } else {
      note.textContent = hasLiveAi ? "AI 문서 생성" : "저장 문서 열기";
    }
  }

  button.title = canOpen
    ? hasLiveAi
      ? `${state.roleFilter} 목표 이력서 AI 생성`
      : `${state.roleFilter} 저장된 목표 이력서 열기`
    : "전체가 아닌 개별 직무를 선택하면 사용할 수 있습니다.";
}

function closeRoleResumeOverlay() {
  if (!state.roleResumeOpen && !state.roleResumeLoading && !state.roleResumeError) return;
  state.roleResumeRequestId += 1;
  abortRoleResumeRequest();
  clearRoleResumeLoadingTicker();
  resetRoleResumeStreamState();
  state.roleResumePdfExporting = false;
  state.roleResumeOpen = false;
  state.roleResumeLoading = false;
  state.roleResumeError = "";
  state.roleResumeNotice = "";
  state.roleResumeNoticeTone = "neutral";
  renderRoleResumeOverlay();
  renderRoleResumeButton();
}

function formatRoleResumeCount(item) {
  return `${escapeHtml(item.label)} · ${item.count}건`;
}

function renderRoleResumeEvidenceList(title, items, extraClass = "") {
  if (!items.length) return "";
  return `
    <section class="role-resume-evidence-card ${extraClass}">
      <p class="role-resume-evidence-title">${escapeHtml(title)}</p>
      <div class="role-resume-chip-group">
        ${items.map((item) => `<span class="role-resume-chip">${formatRoleResumeCount(item)}</span>`).join("")}
      </div>
    </section>
  `;
}

function renderRoleResumeSignalColumns(signalGroups) {
  return Object.entries(ROLE_RESUME_SIGNAL_LABELS)
    .map(([key, label]) => {
      const items = normalizeCountList(signalGroups[key]);
      if (!items.length) return "";
      return renderRoleResumeEvidenceList(label, items, "is-signal");
    })
    .join("");
}

function renderRoleResumePostingSample(sample) {
  const signalLine = uniqueTerms(
    [
      ...(sample.problemSignals || []),
      ...(sample.systemSignals || []),
      ...(sample.workflowSignals || []),
      ...(sample.keywords || []),
    ],
    4,
  );

  return `
    <article class="role-resume-posting-sample">
      <p class="role-resume-posting-company">${escapeHtml(sample.company || "대표 공고")}</p>
      <h4 class="role-resume-posting-title">${escapeHtml(sample.title || "공고명 없음")}</h4>
      ${
        sample.focusLabel
          ? `<p class="role-resume-posting-focus">${escapeHtml(sample.focusLabel)}</p>`
          : ""
      }
      ${
        sample.summary
          ? `<p class="role-resume-posting-summary">${escapeHtml(sample.summary)}</p>`
          : ""
      }
      ${
        signalLine.length
          ? `<div class="role-resume-posting-signals">${signalLine
              .map((item) => `<span>${escapeHtml(item)}</span>`)
              .join("")}</div>`
          : ""
      }
    </article>
  `;
}

function renderRoleResumeProjectEntry(project) {
  const responsibilities = (project.responsibilities || []).slice(0, 3);
  const achievements = (project.achievements || []).slice(0, 3);

  return `
    <article class="role-resume-career-item">
      <div class="role-resume-career-head">
        <div>
          <h5>${escapeHtml(project.title || "Project Title")}</h5>
          ${
            project.meta
              ? `<p class="role-resume-career-meta">${escapeHtml(project.meta)}</p>`
              : ""
          }
        </div>
      </div>
      ${
        project.overview
          ? `<p class="role-resume-career-overview">${escapeHtml(project.overview)}</p>`
          : ""
      }
      ${
        responsibilities.length
          ? `
            <p class="role-resume-career-subtitle">Key responsibilities</p>
            <ul class="role-resume-list compact plain">
              ${responsibilities.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
            </ul>
          `
          : ""
      }
      ${
        achievements.length
          ? `
            <p class="role-resume-career-subtitle">Achievements</p>
            <ul class="role-resume-list compact plain">
              ${achievements.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
            </ul>
          `
          : ""
      }
    </article>
  `;
}

function renderRoleResumeEducationEntry(item) {
  return `
    <div class="role-resume-placeholder-block">
      ${item.title ? `<p class="role-resume-placeholder-title">${escapeHtml(item.title)}</p>` : ""}
      ${item.meta ? `<p class="role-resume-placeholder-note">${escapeHtml(item.meta)}</p>` : ""}
    </div>
  `;
}

function renderRoleResumeSectionRow(label, body, extraClass = "") {
  return `
    <section class="role-resume-section-row ${extraClass}">
      <div class="role-resume-section-label">${escapeHtml(label)}</div>
      <div class="role-resume-section-body">${body}</div>
    </section>
  `;
}

function renderRoleResumeDocument(document, roleLabel) {
  const skillLine = (document.skills || []).join(", ");
  const portfolioItems = (document.portfolio || [])
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join("");
  const projectItems = (document.projects || [])
    .map((project) => renderRoleResumeProjectEntry(project))
    .join("");
  const educationBlock = (document.education || [])
    .map((item) => renderRoleResumeEducationEntry(item))
    .join("");
  return `
    <article class="role-resume-sheet">
      <div class="role-resume-paper-head">
        <div>
          <h3 class="role-resume-placeholder-name">${escapeHtml(document.headline || roleLabel)}</h3>
          ${
            document.subheadline
              ? `<p class="role-resume-paper-subheadline">${escapeHtml(document.subheadline)}</p>`
              : ""
          }
        </div>
      </div>

      ${renderRoleResumeSectionRow(
        "Summary",
        `
          <p class="role-resume-summary-text">${escapeHtml(document.summary || "")}</p>
        `,
      )}

      ${renderRoleResumeSectionRow(
        "Selected Projects",
        `
          <div class="role-resume-career-list">
            ${projectItems}
          </div>
        `,
      )}

      ${renderRoleResumeSectionRow("Education / Preparation", educationBlock)}

      ${renderRoleResumeSectionRow(
        "Key skills",
        `
          <p class="role-resume-skill-line">${escapeHtml(skillLine)}</p>
        `,
      )}

      ${renderRoleResumeSectionRow(
        "Portfolio",
        `
          <ul class="role-resume-list compact plain">
            ${portfolioItems}
          </ul>
        `,
      )}

      ${
        document.footerNote
          ? `<p class="role-resume-footer-note">${escapeHtml(document.footerNote)}</p>`
          : ""
      }
    </article>
  `;
}

function renderRoleResumeOverlay() {
  if (!elements.roleResumeShell || !elements.roleResumePanel || !elements.roleResumeContent) {
    return;
  }

  const visible = state.roleResumeOpen || state.roleResumeLoading || Boolean(state.roleResumeError);
  elements.roleResumeShell.classList.toggle("is-open", visible);
  elements.roleResumeShell.setAttribute("aria-hidden", visible ? "false" : "true");
  document.body.classList.toggle("role-resume-open", visible);

  if (!visible) {
    elements.roleResumeContent.innerHTML = "";
    return;
  }

  if (state.roleResumeLoading) {
    const hasLiveAi = hasLiveRoleResumeConfig();
    elements.roleResumeContent.innerHTML = `
      <div class="role-resume-frame is-loading">
        <div class="role-resume-chrome">
          <button type="button" class="role-resume-close is-floating" aria-label="닫기" data-close-role-resume>X</button>
        </div>
        <div class="role-resume-loading-panel">
          <p class="role-resume-loading-title">${hasLiveAi ? "문서를 생성하고 있습니다" : "저장 문서를 확인하고 있습니다"}</p>
          <p class="role-resume-loading-copy">${
            hasLiveAi
              ? `AI가 ${escapeHtml(state.roleResumeRole || "선택 직무")} 채용 신호를 읽고 실시간으로 문서를 작성하고 있습니다.`
              : `${escapeHtml(state.roleResumeRole || "선택 직무")} 기준으로 이전에 만든 문서를 여는 중입니다. 새 AI 문서는 모델 설정 저장 후 만들 수 있습니다.`
          }</p>
          ${renderRoleResumeLoadingSteps()}
          <div class="role-resume-stream-console">
            <div class="role-resume-stream-section">
              <p class="role-resume-stream-heading">실시간 출력</p>
              ${renderRoleResumeStreamPreview()}
            </div>
          </div>
        </div>
      </div>
    `;
    return;
  }

  if (state.roleResumeError && !state.roleResumeGuides) {
    elements.roleResumeContent.innerHTML = `
      <div class="role-resume-frame">
        <div class="role-resume-chrome">
          <button type="button" class="role-resume-close is-floating" aria-label="닫기" data-close-role-resume>X</button>
        </div>
        <div class="role-resume-loading-panel is-error">
          <p class="role-resume-loading-title">문서를 불러오지 못했습니다</p>
          <p>${escapeHtml(state.roleResumeError)}</p>
          <div class="role-resume-loading-actions">
            <button type="button" class="role-resume-action-button" data-regenerate-role-resume>다시 시도</button>
          </div>
        </div>
      </div>
    `;
    return;
  }

  const guides = state.roleResumeGuides;
  if (!guides) return;

  const { payload } = guides;

  elements.roleResumeContent.innerHTML = `
    <div class="role-resume-frame">
      <div class="role-resume-chrome">
        <button type="button" class="role-resume-close is-floating" aria-label="닫기" data-close-role-resume>X</button>
      </div>

      <div class="role-resume-scroll">
        ${renderRoleResumeToolbar()}
        <section class="role-resume-stack">
          ${payload.document ? renderRoleResumeDocument(payload.document, guides.role || state.roleResumeRole || "선택 직무") : ""}
        </section>
      </div>
    </div>
  `;
}

async function requestRoleResumeDocument({ forceRefresh = true, preserveExisting = false } = {}) {
  if (!canOpenRoleResumeGuides()) {
    setStatus(
      state.roleFilter === "기타"
        ? "기타 묶음은 시장 신호가 섞여 있어 목표 이력서 생성 대상에서 제외했습니다."
        : "전체가 아닌 개별 직무를 먼저 선택해주세요.",
    );
    return;
  }

  const role = state.roleFilter;
  const activityFilter = state.activityFilter;
  const roleResumeConfig = readRoleResumeConfig();
  const hasLiveAi = roleResumeConfig ? hasUsableModelConfig(roleResumeConfig) : true;
  const requestId = state.roleResumeRequestId + 1;
  const previousGuides = preserveExisting ? state.roleResumeGuides : null;

  state.roleResumeRequestId = requestId;
  state.roleResumeRole = role;
  state.roleResumeActivityMode = activityFilter;
  state.roleResumeGuides = preserveExisting ? previousGuides : null;
  state.roleResumeError = "";
  state.roleResumeLoading = true;
  state.roleResumeOpen = true;
  state.roleResumeLoadingMode = forceRefresh ? "regenerate" : "open";
  state.roleResumeLoadingStepIndex = 0;
  state.roleResumeNotice = "";
  state.roleResumeNoticeTone = "neutral";
  resetRoleResumeStreamState();
  pushRoleResumeStreamLog("요청을 보내고 있습니다.");
  hideCompanyHoverPopover();
  closeClusterDrawer();
  abortRoleResumeRequest();
  roleResumeAbortController = new AbortController();
  renderRoleResumeOverlay();
  renderRoleResumeButton();
  setStatus(hasLiveAi ? `${role} 목표 이력서를 생성하는 중...` : `${role} 저장 문서를 여는 중...`);
  await waitForNextPaint();

  try {
    let finalResult = null;
    await postEventStream("/api/role-resume-guides/stream", {
      role,
      activityFilter,
      config: roleResumeConfig,
      forceRefresh,
    }, {
      signal: roleResumeAbortController.signal,
      onEvent(event, payload) {
        if (state.roleResumeRequestId !== requestId) return;
        if (event === "status") {
          if (payload.message) {
            syncRoleResumePhaseFromMessage(payload.message);
            pushRoleResumeStreamLog(payload.message);
          }
          renderRoleResumeOverlay();
          return;
        }
        if (event === "token") {
          appendRoleResumeStreamPreview(payload.text || payload.raw || "");
          renderRoleResumeOverlay();
          return;
        }
        if (event === "final") {
          finalResult = payload;
          const normalized = normalizeRoleResumeResponse(payload);
          state.roleResumeGuides = normalized;
          state.roleResumeLoading = false;
          state.roleResumeError = "";
          state.roleResumeOpen = true;
          state.roleResumeNotice = normalized.stale
            ? hasLiveAi
              ? "새 문서 생성에 실패해 마지막 저장 문서를 열었습니다."
              : "실시간 AI 모델 설정이 없어 저장된 문서를 열었습니다."
            : "";
          state.roleResumeNoticeTone = normalized.stale ? "error" : "neutral";
          pushRoleResumeStreamLog("문서 렌더링을 준비하고 있습니다.");
          renderRoleResumeOverlay();
          renderRoleResumeButton();
          return;
        }
        if (event === "error") {
          throw new Error(payload.error || "스트림 생성 실패");
        }
      },
    });
    if (state.roleResumeRequestId !== requestId) return;
    if (!finalResult) {
      finalResult = await postJson("/api/role-resume-guides", {
        role,
        activityFilter,
        config: roleResumeConfig,
        forceRefresh: false,
      });
    }
    roleResumeAbortController = null;
    clearRoleResumeLoadingTicker();
    const normalized = normalizeRoleResumeResponse(finalResult);
    state.roleResumeGuides = normalized;
    state.roleResumeLoading = false;
    state.roleResumeError = "";
    state.roleResumeOpen = true;
    state.roleResumeNotice = normalized.stale
      ? hasLiveAi
        ? "새 문서 생성에 실패해 마지막 저장 문서를 열었습니다."
        : "실시간 AI 모델 설정이 없어 저장된 문서를 열었습니다."
      : "";
    state.roleResumeNoticeTone = normalized.stale ? "error" : "neutral";
    renderRoleResumeOverlay();
    renderRoleResumeButton();
    setStatus(`${role} 목표 이력서를 생성했습니다.`);
  } catch (error) {
    if (state.roleResumeRequestId !== requestId) return;
    if (error?.name === "AbortError") return;
    roleResumeAbortController = null;
    clearRoleResumeLoadingTicker();
    state.roleResumeLoading = false;
    if (previousGuides) {
      state.roleResumeGuides = previousGuides;
      state.roleResumeError = "";
      state.roleResumeOpen = true;
      state.roleResumeNotice = `재생성에 실패해 기존 문서를 유지했습니다. ${error.message}`;
      state.roleResumeNoticeTone = "error";
    } else {
      state.roleResumeError = error.message;
      state.roleResumeOpen = true;
      state.roleResumeNotice = "";
      state.roleResumeNoticeTone = "neutral";
    }
    renderRoleResumeOverlay();
    renderRoleResumeButton();
    setStatus(error.message);
  }
}

async function openRoleResumeOverlay() {
  return requestRoleResumeDocument({ forceRefresh: true, preserveExisting: false });
}

async function regenerateRoleResumeOverlay() {
  return requestRoleResumeDocument({ forceRefresh: true, preserveExisting: true });
}

function renderRoleTabs() {
  const filters = roleFilters();
  if (!filters.length) {
    elements.roleTabs.innerHTML = "";
    return;
  }

  if (!new Set(filters.map((item) => item.name)).has(state.roleFilter)) {
    state.roleFilter = "전체";
  }

  elements.roleTabs.innerHTML = filters
    .map((item) => {
      const meta = ROLE_ICON_META[item.name] || { icon: "icon-all", badge: item.name };
      return `
        <button
          type="button"
          class="nav-item role-tile ${item.name === state.roleFilter ? "active" : ""}"
          data-role-filter="${escapeHtml(item.name)}"
        >
          <span class="role-tile-icon ${meta.icon}" aria-hidden="true">
            <span class="role-icon-shape"></span>
            <span class="role-icon-shape secondary"></span>
            <span class="role-icon-shape tertiary"></span>
          </span>
          <span class="role-tile-copy">
            <span class="role-tile-name">${escapeHtml(item.name)}</span>
            <span class="role-tile-badge">${escapeHtml(meta.badge)}</span>
          </span>
          <span class="nav-count">${item.count}</span>
        </button>
      `;
    })
    .join("");
}

function renderActivityTabs() {
  const buttons = elements.activityTabs.querySelectorAll("[data-activity-filter]");
  buttons.forEach((button) => {
    button.classList.toggle("active", button.dataset.activityFilter === state.activityFilter);
  });
}

function keywordTone(keyword) {
  const value = String(keyword || "").toLowerCase();
  if (["llm", "rag", "멀티모달", "딥러닝", "onnx", "비전", "최적화", "포팅"].some((term) => value.includes(term))) {
    return "tone-ai";
  }
  if (["data", "데이터", "etl", "인프라", "클라우드", "sql", "파이프라인", "mlops"].some((term) => value.includes(term))) {
    return "tone-data";
  }
  if (["금융", "교육", "제조", "의료", "고객", "서비스", "제품", "병원"].some((term) => value.includes(term))) {
    return "tone-domain";
  }
  if (["분석", "실험", "평가", "검증", "지표", "예측", "시뮬레이션"].some((term) => value.includes(term))) {
    return "tone-analysis";
  }
  return "tone-neutral";
}

function highlightText(text, keywords) {
  const source = String(text || "");
  const normalizedKeywords = (keywords || [])
    .map((keyword) => ({
      text: String(keyword || "").trim(),
      tone: keywordTone(keyword),
    }))
    .filter((keyword) => keyword.text)
    .sort((left, right) => right.text.length - left.text.length);

  if (!source || !normalizedKeywords.length) {
    return escapeHtml(source);
  }

  const pattern = normalizedKeywords
    .map((keyword) => escapeRegExp(keyword.text))
    .filter(Boolean)
    .join("|");
  if (!pattern) {
    return escapeHtml(source);
  }

  const regex = new RegExp(`(${pattern})`, "giu");
  return source
    .split(regex)
    .filter((part) => part !== "")
    .map((part) => {
      const matched = normalizedKeywords.find(
        (keyword) => keyword.text.toLowerCase() === part.toLowerCase(),
      );
      if (matched) {
        return `<mark class="keyword-highlight ${matched.tone}">${escapeHtml(part)}</mark>`;
      }
      return escapeHtml(part);
    })
    .join("");
}

function companyTokens(company) {
  return new Set(
    String(company || "").match(/[A-Za-z][A-Za-z0-9]+|[가-힣]{2,}/g) || [],
  );
}

function isWeakFieldTerm(term, sectionId = "") {
  const raw = String(term || "").trim();
  const key = canonical(raw);
  if (!raw || !key) return true;
  if (FIELD_STOPWORDS.has(key) || WEAK_FIELD_TERM_KEYS.has(key)) return true;
  if (/(지사|오피스|센터|홈원)$/.test(raw)) return true;
  if (/(모집|채용)$/.test(raw) && raw.length <= 24) return true;
  if (TERM_ENDING_PATTERNS.some((pattern) => pattern.test(raw))) return true;
  if (/[가-힣]{2,}(의|를|을|이|가|와|과|에|에서|으로|로)$/.test(raw)) return true;
  if (/^[0-9]+$/.test(raw)) return true;
  if (/^[가-힣]{2}$/.test(raw) && !ALLOWED_SHORT_TERM_KEYS.has(key)) return true;
  if (/^[A-Za-z]+$/.test(raw) && raw.length <= 3 && !ALLOWED_SHORT_TERM_KEYS.has(key)) return true;
  if (sectionId !== "skills" && NON_SKILL_GENERIC_KEYS.has(key)) return true;
  return false;
}

function collectAliasTerms(text, sectionId) {
  const compactText = canonical(text);
  const result = [];
  const seen = new Set();

  for (const alias of TERM_ALIASES) {
    const matched = alias.patterns.some((pattern) => compactText.includes(canonical(pattern)));
    if (!matched) continue;
    const label = alias.label;
    const key = canonical(label);
    if (!key || seen.has(key) || isWeakFieldTerm(label, sectionId)) continue;
    seen.add(key);
    result.push(label);
  }
  return result;
}

function extractTerms(values, company, sectionId = "") {
  const joined = values.join(" ");
  const companySet = new Set(Array.from(companyTokens(company)).map((token) => canonical(token)));
  const seen = new Set();
  const terms = [];

  for (const aliasTerm of collectAliasTerms(joined, sectionId)) {
    const key = canonical(aliasTerm);
    if (!key || seen.has(key) || companySet.has(key)) {
      continue;
    }
    seen.add(key);
    terms.push(aliasTerm);
  }

  for (const part of joined.match(/[A-Za-z][A-Za-z0-9+#./-]{1,}|[가-힣]{2,}/g) || []) {
    const normalizedTerm = normalizeTermLabel(part);
    const key = canonical(normalizedTerm);
    if (
      !key
      || seen.has(key)
      || FIELD_STOPWORDS.has(key)
      || companySet.has(key)
      || key.length < 2
      || isWeakFieldTerm(normalizedTerm, sectionId)
    ) {
      continue;
    }
    seen.add(key);
    terms.push(normalizedTerm);
  }

  return terms;
}

function sectionRawTerms(row, section) {
  const rawValues = section.values(row).map((value) => String(value || "").trim()).filter(Boolean);
  return dedupeTerms(extractTerms(rawValues, row.company || "", section.id));
}

function pickTheme(values, terms) {
  const textBlob = values.join(" ").toLowerCase();
  let bestTheme = SECTION_THEMES[SECTION_THEMES.length - 1];
  let bestScore = -1;

  for (const theme of SECTION_THEMES.slice(0, -1)) {
    let score = 0;
    for (const token of theme.tokens) {
      const compact = canonical(token);
      if (
        terms.some((term) => {
          const termCompact = canonical(term);
          return termCompact === compact || termCompact.includes(compact) || compact.includes(termCompact);
        })
      ) {
        score += 3;
      }
      if (compact && textBlob.includes(token.toLowerCase())) {
        score += 1;
      }
    }
    if (score > bestScore) {
      bestTheme = theme;
      bestScore = score;
    }
  }

  return bestScore <= 0 ? SECTION_THEMES[SECTION_THEMES.length - 1] : bestTheme;
}

function dedupeTerms(values) {
  const seen = new Set();
  const output = [];
  values.forEach((value) => {
    const label = String(value || "").trim();
    const key = canonical(label);
    if (!key || seen.has(key)) return;
    seen.add(key);
    output.push(label);
  });
  return output;
}

function buildClusterCopy(section, keywords) {
  const joined = keywords.slice(0, 3).join(" · ");
  if (!joined) {
    return `${section.label}에서 반복되는 신호를 기반으로 정리한 군집입니다.`;
  }
  if (section.id === "tasks") {
    return `${joined} 중심의 업무 문장이 반복되는 공고 묶음입니다.`;
  }
  if (section.id === "requirements") {
    return `${joined} 중심의 자격 조건이 반복되는 공고 묶음입니다.`;
  }
  if (section.id === "preferred") {
    return `${joined} 중심의 우대 배경이 반복되는 공고 묶음입니다.`;
  }
  if (section.id === "skills") {
    return `${joined} 조합이 함께 등장하는 기술 묶음입니다.`;
  }
  return `${joined} 신호를 중심으로 한 군집입니다.`;
}

function buildClusterReason(section, keywords, sampleLines = []) {
  const strongKeywords = (keywords || []).filter((term) => !isWeakFieldTerm(term, section.id));
  if (strongKeywords.length) {
    return `${strongKeywords.slice(0, 3).join(" · ")} 표현이 여러 공고에서 반복됩니다.`;
  }

  const sample = (sampleLines || []).find((line) => line && line.length >= 8);
  if (sample) {
    return sample;
  }
  return `${section.label} 안에서 비슷한 표현을 중심으로 정리한 그룹입니다.`;
}

function chooseClusterLabel(section, keywords, fallbackLabel) {
  const strongKeywords = normalizeClusterLabelParts(
    (keywords || []).filter((term) => !isWeakFieldTerm(term, section.id)),
  );
  if (strongKeywords.length >= 2) {
    return strongKeywords.slice(0, 2).join(" · ");
  }
  if (strongKeywords.length === 1) {
    return strongKeywords[0];
  }
  return fallbackLabel || `${section.label} 그룹`;
}

function clusterLabelScore(term) {
  const raw = String(term || "").trim();
  const key = canonical(raw);
  if (!key) return -999;

  let score = Math.min(raw.length, 18);
  if (BROAD_CLUSTER_LABEL_KEYS.has(key)) {
    score -= 12;
  }
  if (raw.includes(" ")) {
    score += 2;
  }
  if (/[A-Z]/.test(raw)) {
    score += 1;
  }
  return score;
}

function normalizeClusterLabelParts(parts) {
  const deduped = [];
  const seen = new Set();

  (parts || []).forEach((part) => {
    const raw = String(part || "").trim();
    const key = canonical(raw);
    if (!raw || !key || seen.has(key)) return;
    seen.add(key);
    deduped.push(raw);
  });

  deduped.sort((left, right) => {
    const diff = clusterLabelScore(right) - clusterLabelScore(left);
    if (diff !== 0) return diff;
    return left.localeCompare(right);
  });

  return deduped;
}

function canonicalClusterLabelKey(label) {
  const parts = String(label || "")
    .split("·")
    .map((part) => part.trim())
    .filter(Boolean);
  return normalizeClusterLabelParts(parts).map((part) => canonical(part)).join("|");
}

function buildEvidence(values, keywords) {
  const lines = values
    .map((value) => String(value || "").replace(/\s+/g, " ").trim())
    .filter(Boolean);
  const matched = lines.find((line) =>
    keywords.some((keyword) => canonical(line).includes(canonical(keyword))),
  );
  const source = matched || lines[0] || "";
  if (!source) return "";
  return source.length > 88 ? `${source.slice(0, 88).trim()}...` : source;
}

function sectionStructuredTerms(row, sectionId, rawTerms = []) {
  const sectionFacetSource = (row.sectionSignalFacets || {})[sectionId];
  const sectionFacets = normalizeSignalFacetsPayload(sectionFacetSource);
  if (sectionFacetSource) {
    const facetTerms = uniqueTerms(
      [
        ...sectionFacets.keyword,
        ...sectionFacets.tag,
        ...sectionFacets.context,
      ],
      10,
    ).filter((term) => !isWeakFieldTerm(term, sectionId));

    if (facetTerms.length >= 2 || rawTerms.length === 0 || sectionId !== "skills") {
      return facetTerms;
    }

    return uniqueTerms(
      [
        ...facetTerms,
        ...rawTerms,
      ],
      10,
    ).filter((term) => !isWeakFieldTerm(term, sectionId));
  }

  const structured = normalizeStructuredSignalsPayload(row.structuredSignals);

  const bySection = {
    detailBody: [
      ...rawTerms,
      ...structured.problemSignals,
      ...structured.domainSignals,
      ...structured.systemSignals,
      ...structured.modelSignals,
      ...structured.dataSignals,
    ],
    tasks: [
      ...rawTerms,
      ...structured.problemSignals,
      ...structured.workflowSignals,
      ...structured.systemSignals,
    ],
    requirements: [
      ...rawTerms,
      ...structured.modelSignals,
      ...structured.systemSignals,
      ...structured.dataSignals,
      ...structured.domainSignals,
    ],
    preferred: [
      ...rawTerms,
      ...structured.domainSignals,
      ...structured.dataSignals,
      ...structured.workflowSignals,
    ],
    skills: [
      ...rawTerms,
      ...structured.modelSignals,
      ...structured.dataSignals,
      ...structured.systemSignals,
    ],
  };

  return uniqueTerms(bySection[sectionId] || [], 10).filter((term) => !isWeakFieldTerm(term, sectionId));
}

function buildDetailSectionClusters(rows) {
  const clusterLookup = new Map((state.board?.clusters || []).map((cluster) => [cluster.id, cluster]));
  const grouped = new Map();

  rows.forEach((row) => {
    const cluster = clusterLookup.get(row.clusterId);
    if (!cluster) return;

    if (!grouped.has(cluster.id)) {
      grouped.set(cluster.id, {
        id: cluster.id,
        tone: cluster.tone,
        label: cluster.label,
        description: cluster.description,
        reason: cluster.reason,
        keywords: cluster.keywords || [],
        postingCount: 0,
        companies: new Set(),
        sampleCompanies: [],
        postingIds: new Set(),
      });
    }

    const bucket = grouped.get(cluster.id);
    bucket.postingCount += 1;
    bucket.postingIds.add(row.id);
    if (row.company) {
      bucket.companies.add(row.company);
      if (!bucket.sampleCompanies.includes(row.company) && bucket.sampleCompanies.length < 4) {
        bucket.sampleCompanies.push(row.company);
      }
    }
  });

  return Array.from(grouped.values())
    .map((bucket) => ({
      ...bucket,
      companyCount: bucket.companies.size,
      postingIds: Array.from(bucket.postingIds),
    }))
    .sort((left, right) => right.postingCount - left.postingCount || left.label.localeCompare(right.label))
    .slice(0, FIELD_SECTIONS[0].maxClusters);
}

function buildDocuments(rows, section) {
  const documents = [];
  const support = new Map();

  rows.forEach((row) => {
    const rawValues = section.values(row).map((value) => String(value || "").trim()).filter(Boolean);
    const rawTerms = sectionRawTerms(row, section);
    const signalValues = sectionStructuredTerms(row, section.id, rawTerms);
    const terms = dedupeTerms(
      signalValues.length >= 2
        ? signalValues
        : (signalValues.length ? [...signalValues, ...(section.id === "skills" ? rawTerms : [])] : (section.id === "skills" ? rawTerms : [])),
    );
    if (!terms.length) return;

    const themeInputs = signalValues.length ? signalValues : rawTerms;
    const theme = pickTheme(themeInputs.length ? themeInputs : rawValues, terms);
    documents.push({ row, values: rawValues.length ? rawValues : themeInputs, terms, theme });
    terms.forEach((term) => {
      support.set(term, (support.get(term) || 0) + 1);
    });
  });

  return { documents, support };
}

function scoreTerm(term, support, section) {
  if (isWeakFieldTerm(term, section.id)) {
    return -999;
  }
  let score = (support.get(term) || 0) * 10;
  score += Math.min(String(term || "").length, 12);
  if (/^[A-Z0-9+.#/-]+$/.test(term)) {
    score += 4;
  }
  if (section.id === "skills") {
    score += 5;
  }
  if (canonical(term) === canonical("전문연구요원")) {
    score += 2;
  }
  if (["석사", "박사", "학사", "학력", "학위", "전공"].includes(term)) {
    score -= 18;
  }
  if (section.id !== "skills" && NON_SKILL_GENERIC_KEYS.has(canonical(term))) {
    score -= 10;
  }
  return score;
}

function buildSeedClusters(rows, section) {
  const { documents, support } = buildDocuments(rows, section);
  if (!documents.length) {
    return [];
  }

  const minSupport = documents.length >= 60 ? 4 : documents.length >= 24 ? 3 : 2;
  const buckets = new Map();

  documents.forEach((doc) => {
    const rankedTerms = [...doc.terms].sort((left, right) => {
      const scoreDiff = scoreTerm(right, support, section) - scoreTerm(left, support, section);
      if (scoreDiff !== 0) return scoreDiff;
      return left.localeCompare(right);
    });

    const seed =
      rankedTerms.find((term) => (support.get(term) || 0) >= minSupport && !isWeakFieldTerm(term, section.id))
      || rankedTerms.find((term) => !isWeakFieldTerm(term, section.id))
      || rankedTerms[0];
    if (!seed) return;

    const key = canonical(seed);
    if (!buckets.has(key)) {
      buckets.set(key, {
        id: `${section.id}-${key}`,
        seed,
        postingCount: 0,
        companies: new Set(),
        sampleCompanies: [],
        keywordCounts: new Map(),
        toneCounts: new Map(),
        sampleLines: [],
        postingIds: new Set(),
      });
    }

    const bucket = buckets.get(key);
    bucket.postingCount += 1;
    bucket.postingIds.add(doc.row.id);
    bucket.toneCounts.set(doc.theme.tone, (bucket.toneCounts.get(doc.theme.tone) || 0) + 1);

    if (doc.row.company) {
      bucket.companies.add(doc.row.company);
      if (!bucket.sampleCompanies.includes(doc.row.company) && bucket.sampleCompanies.length < 4) {
        bucket.sampleCompanies.push(doc.row.company);
      }
    }

    doc.terms.slice(0, 8).forEach((term, index) => {
      if (isWeakFieldTerm(term, section.id)) return;
      const score = Math.max(7 - index, 1) + Math.min(support.get(term) || 0, 4);
      bucket.keywordCounts.set(term, (bucket.keywordCounts.get(term) || 0) + score);
    });

    const sample = buildEvidence(doc.values, rankedTerms.slice(0, 3));
    if (sample && !bucket.sampleLines.includes(sample) && bucket.sampleLines.length < 2) {
      bucket.sampleLines.push(sample);
    }
  });

  return Array.from(buckets.values())
    .filter((bucket) => bucket.postingCount >= minSupport || bucket.postingCount >= 2)
    .map((bucket) => {
      const keywords = Array.from(bucket.keywordCounts.entries())
        .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
        .slice(0, 5)
        .map(([term]) => term)
        .filter((term) => !isWeakFieldTerm(term, section.id));
      const tone =
        Array.from(bucket.toneCounts.entries()).sort((left, right) => right[1] - left[1])[0]?.[0] ||
        "cluster-g";
      const label = chooseClusterLabel(section, keywords, bucket.seed);
      return {
        id: bucket.id,
        tone,
        label,
        description: buildClusterCopy(section, keywords.length ? keywords : [bucket.seed]),
        reason: buildClusterReason(section, keywords.length ? keywords : [bucket.seed], bucket.sampleLines),
        keywords,
        postingCount: bucket.postingCount,
        companyCount: bucket.companies.size,
        sampleCompanies: bucket.sampleCompanies,
        postingIds: Array.from(bucket.postingIds),
      };
    })
    .sort((left, right) => right.postingCount - left.postingCount || left.label.localeCompare(right.label))
    .slice(0, section.maxClusters);
}

function buildThemeClusters(rows, section) {
  const buckets = new Map();

  rows.forEach((row) => {
    const values = section.values(row).map((value) => String(value || "").trim()).filter(Boolean);
    const rawTerms = sectionRawTerms(row, section);
    const signalValues = sectionStructuredTerms(row, section.id, rawTerms);
    const terms = dedupeTerms(
      signalValues.length >= 2
        ? signalValues
        : (signalValues.length ? [...signalValues, ...(section.id === "skills" ? rawTerms : [])] : (section.id === "skills" ? rawTerms : [])),
    );
    if (!terms.length) return;

    const themeValues = signalValues.length ? signalValues : (rawTerms.length ? rawTerms : values);
    const theme = pickTheme(themeValues, terms);
    if (!buckets.has(theme.id)) {
      buckets.set(theme.id, {
        id: theme.id,
        tone: theme.tone,
        label: theme.label,
        postingCount: 0,
        companies: new Set(),
        sampleCompanies: [],
        keywordCounts: new Map(),
        sampleLines: [],
        postingIds: new Set(),
      });
    }

    const bucket = buckets.get(theme.id);
    bucket.postingCount += 1;
    bucket.postingIds.add(row.id);
    if (row.company) {
      bucket.companies.add(row.company);
      if (!bucket.sampleCompanies.includes(row.company) && bucket.sampleCompanies.length < 4) {
        bucket.sampleCompanies.push(row.company);
      }
    }

    terms.slice(0, 8).forEach((term, index) => {
      if (isWeakFieldTerm(term, section.id)) return;
      const score = Math.max(5 - index, 1);
      bucket.keywordCounts.set(term, (bucket.keywordCounts.get(term) || 0) + score);
    });

    const evidence = buildEvidence(values.length ? values : themeValues, terms.slice(0, 3));
    if (evidence && !bucket.sampleLines.includes(evidence) && bucket.sampleLines.length < 2) {
      bucket.sampleLines.push(evidence);
    }
  });

  return Array.from(buckets.values())
    .map((bucket) => {
      const keywords = Array.from(bucket.keywordCounts.entries())
        .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
        .slice(0, 4)
        .map(([term]) => term)
        .filter((term) => !isWeakFieldTerm(term, section.id));
      return {
        id: bucket.id,
        tone: bucket.tone,
        label: chooseClusterLabel(section, keywords, bucket.label),
        description: buildClusterCopy(section, keywords.length ? keywords : [bucket.label]),
        reason: buildClusterReason(section, keywords.length ? keywords : [bucket.label], bucket.sampleLines),
        keywords,
        postingCount: bucket.postingCount,
        companyCount: bucket.companies.size,
        sampleCompanies: bucket.sampleCompanies,
        postingIds: Array.from(bucket.postingIds),
      };
    })
    .sort((left, right) => right.postingCount - left.postingCount || left.label.localeCompare(right.label))
    .slice(0, section.maxClusters);
}

function buildSectionClusters(rows, section) {
  const uniqueByLabel = (clusters) => {
    const seen = new Set();
    return (clusters || []).filter((cluster) => {
      const key = canonicalClusterLabelKey(cluster.label || "");
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  };

  if (section.id === "detailBody") {
    const seededClusters = buildSeedClusters(rows, section);
    const themedClusters = buildThemeClusters(rows, section);
    return uniqueByLabel([...seededClusters, ...themedClusters])
      .sort((left, right) => right.postingCount - left.postingCount || left.label.localeCompare(right.label))
      .slice(0, section.maxClusters);
  }

  const seededClusters = buildSeedClusters(rows, section);
  if (seededClusters.length >= 3) {
    return uniqueByLabel(seededClusters);
  }
  return uniqueByLabel(buildThemeClusters(rows, section));
}

function renderClusterCard(cluster, section, emphasize) {
  const companies = (cluster.sampleCompanies || [])
    .slice(0, 4)
    .map((company) => `<span class="company-chip">${escapeHtml(company)}</span>`)
    .join("");
  const clusterKey = buildClusterKey(section.id, cluster.id);
  return `
    <div class="field-cluster-node ${cluster.tone}">
      <article
        class="field-cluster-card ${cluster.tone} ${emphasize ? "is-emphasis" : ""} ${state.activeClusterKey === clusterKey ? "is-open" : ""}"
        role="button"
        tabindex="0"
        data-cluster-key="${escapeHtml(clusterKey)}"
        aria-expanded="${state.activeClusterKey === clusterKey ? "true" : "false"}"
        aria-controls="cluster-drawer-panel"
      >
        <div class="field-cluster-card-body">
          <div class="field-cluster-card-meta">
            <span class="field-cluster-kicker">Hire Atlas</span>
            <span class="field-cluster-code">Signal Cluster</span>
          </div>
          <div class="field-cluster-card-head">
            <div class="field-cluster-title-row">
              <span class="field-cluster-dot ${cluster.tone}" aria-hidden="true"></span>
              <span class="field-cluster-title">${escapeHtml(cluster.label)}</span>
            </div>
            <div class="field-cluster-stats">
              <span>${cluster.postingCount} 공고</span>
              <span>${cluster.companyCount} 기업</span>
            </div>
          </div>
          <p class="field-cluster-copy">${escapeHtml(cluster.description || "")}</p>
          <p class="field-cluster-reason">${highlightText(cluster.reason || "", cluster.keywords || [])}</p>
          <div class="field-cluster-keywords">
            ${(cluster.keywords || [])
              .slice(0, 5)
              .map((keyword) => `<span class="keyword-chip ${cluster.tone}">${escapeHtml(keyword)}</span>`)
              .join("")}
          </div>
          ${
            companies
              ? `
          <footer class="field-cluster-footer">
            <p class="field-cluster-footer-label">Representative Companies</p>
            <div class="field-cluster-companies">${companies}</div>
          </footer>
          `
              : ""
          }
        </div>
      </article>
    </div>
  `;
}

function renderFieldSection(section, rows, index, total) {
  const clusters = buildSectionClusters(rows, section);
  clusters.forEach((cluster) => {
    const clusterKey = buildClusterKey(section.id, cluster.id);
    state.clusterMap.set(clusterKey, {
      ...cluster,
      sectionId: section.id,
      sectionLabel: section.label,
    });
  });
  const coveredRows = rows.filter((row) =>
    section.values(row).some((value) => String(value || "").trim()),
  ).length;
  const shellClasses = [
    "analysis-section-shell",
    `field-${section.id}`,
    index === 0 ? "is-first" : "",
    index === total - 1 ? "is-last" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return `
    <div class="${shellClasses}">
      <span class="section-flow top" aria-hidden="true"></span>
      <span class="section-flow bottom" aria-hidden="true"></span>
      <section class="analysis-section field-${section.id} ${index === 0 ? "is-primary" : ""}">
        <div class="analysis-section-head">
          <div>
            <p class="analysis-section-eyebrow">${escapeHtml(section.label)}</p>
          </div>
          <div class="analysis-section-metrics">
            <span class="analysis-metric-pill" aria-label="${coveredRows}개 공고">
              <span class="analysis-metric-pill-core">
                <strong aria-hidden="true">${renderAnimatedMetricText(coveredRows, "is-number")}</strong>
                <em aria-hidden="true">${renderAnimatedMetricText("공고", "is-label")}</em>
              </span>
            </span>
            <span class="analysis-metric-pill" aria-label="${clusters.length}개 묶음">
              <span class="analysis-metric-pill-core">
                <strong aria-hidden="true">${renderAnimatedMetricText(clusters.length, "is-number")}</strong>
                <em aria-hidden="true">${renderAnimatedMetricText("묶음", "is-label")}</em>
              </span>
            </span>
          </div>
        </div>
        <div class="analysis-section-canvas ${index === 0 ? "is-primary" : ""}">
          ${
            clusters.length
              ? clusters
                  .map((cluster, clusterIndex) => renderClusterCard(cluster, section, index === 0 && clusterIndex === 0))
                  .join("")
              : `<div class="field-section-empty">이 필드에서 유의미한 군집을 아직 만들지 못했습니다.</div>`
          }
        </div>
      </section>
    </div>
  `;
}

function filterSemanticBundlesForCurrentRows() {
  const rows = currentRows();
  const rowById = new Map(rows.map((row) => [row.id, row]));
  const sourceBundles =
    state.roleFilter !== "전체"
      ? (state.board?.semanticBundlesByRole || {})[state.roleFilter] || []
      : state.board?.semanticBundles || [];
  return sourceBundles
    .map((bundle) => {
      const postingIds = (bundle.postingIds || []).filter((id) => rowById.has(id));
      if (!postingIds.length) return null;
      const companies = uniqueTerms(postingIds.map((id) => rowById.get(id)?.company).filter(Boolean), 6);
      if (state.roleFilter !== "전체" && (postingIds.length < 2 || companies.length < 2)) {
        return null;
      }
      return {
        ...bundle,
        postingIds,
        postingCount: postingIds.length,
        companyCount: companies.length,
        sampleCompanies: companies.slice(0, 4),
      };
    })
    .filter(Boolean)
    .slice(0, 12);
}

function semanticBundleToCluster(bundle, index) {
  const tone = CLUSTER_TONES[index % CLUSTER_TONES.length];
  const keywords = uniqueTerms(
    [
      ...(bundle.axes || []),
      ...(bundle.skills || []),
      ...(bundle.evidenceTerms || []),
    ],
    5,
  );
  return {
    id: bundle.id || `semantic-${index + 1}`,
    tone,
    label: bundle.label || "의미 조합",
    description: bundle.thesis || "공고 안에서 함께 반복되는 문제와 기술 조합입니다.",
    reason: bundle.thesis || "",
    keywords,
    postingCount: bundle.postingCount,
    companyCount: bundle.companyCount,
    sampleCompanies: bundle.sampleCompanies || [],
    postingIds: bundle.postingIds || [],
  };
}

function renderSemanticBundleCard(cluster, clusterKey, emphasize) {
  const companies = (cluster.sampleCompanies || [])
    .slice(0, 4)
    .map((company) => `<span class="company-chip">${escapeHtml(company)}</span>`)
    .join("");

  return `
    <article
      class="semantic-bundle-card ${cluster.tone} ${emphasize ? "is-emphasis" : ""} ${state.activeClusterKey === clusterKey ? "is-open" : ""}"
      role="button"
      tabindex="0"
      data-cluster-key="${escapeHtml(clusterKey)}"
      aria-expanded="${state.activeClusterKey === clusterKey ? "true" : "false"}"
      aria-controls="cluster-drawer-panel"
    >
      <div class="semantic-bundle-card-meta">
        <span class="field-cluster-kicker">Hire Atlas</span>
        <span class="field-cluster-code">Meaning Bundle</span>
      </div>
      <div class="semantic-bundle-card-head">
        <div class="field-cluster-title-row">
          <span class="field-cluster-dot ${cluster.tone}" aria-hidden="true"></span>
          <span class="semantic-bundle-title">${escapeHtml(cluster.label)}</span>
        </div>
        <div class="field-cluster-stats">
          <span>${cluster.postingCount} 공고</span>
          <span>${cluster.companyCount} 기업</span>
        </div>
      </div>
      <p class="semantic-bundle-copy">${escapeHtml(cluster.description || "")}</p>
      <div class="field-cluster-keywords">
        ${(cluster.keywords || [])
          .slice(0, 5)
          .map((keyword) => `<span class="keyword-chip ${cluster.tone}">${escapeHtml(keyword)}</span>`)
          .join("")}
      </div>
      ${
        companies
          ? `
      <footer class="semantic-bundle-footer">
        <p class="field-cluster-footer-label">Representative Companies</p>
        <div class="field-cluster-companies">${companies}</div>
      </footer>
      `
          : ""
      }
    </article>
  `;
}

function renderSemanticBundles() {
  if (!elements.semanticBundles) return;
  const rows = currentRows();
  if (!rows.length) {
    elements.semanticBundles.innerHTML = "";
    return;
  }

  const bundles = filterSemanticBundlesForCurrentRows();
  const trendLead = `
    <p class="semantic-bundle-lead">
      <span class="semantic-bundle-lead-title">${escapeHtml(SEMANTIC_BUNDLE_SECTION.label)}</span>
      <span class="semantic-bundle-lead-dot" aria-hidden="true">·</span>
      <span class="semantic-bundle-lead-copy">지원할 공고를 고를 때는 함께 반복되는 문제, 기술, 운영 맥락을 보면 준비 방향이 더 또렷해집니다.</span>
    </p>
  `;
  if (!bundles.length) {
    elements.semanticBundles.innerHTML = `
      <div class="analysis-section-shell semantic-bundle-shell is-first">
        <section class="analysis-section semantic-bundle-section">
          <div class="analysis-section-head">
            <div>
              ${trendLead}
              <p class="analysis-section-copy">아직 이 조건에서는 충분히 반복되는 채용 흐름이 없습니다.</p>
            </div>
          </div>
        </section>
        <div class="semantic-bundle-divider" aria-hidden="true"></div>
      </div>
    `;
    return;
  }

  const coveredRows = new Set(bundles.flatMap((bundle) => bundle.postingIds || [])).size;
  const clusters = bundles.map((bundle, index) => semanticBundleToCluster(bundle, index));
  const clusterCards = clusters.map((cluster, index) => {
    const clusterKey = buildClusterKey(SEMANTIC_BUNDLE_SECTION.id, cluster.id);
    state.clusterMap.set(clusterKey, {
      ...cluster,
      sectionId: SEMANTIC_BUNDLE_SECTION.id,
      sectionLabel: SEMANTIC_BUNDLE_SECTION.label,
    });
    return renderSemanticBundleCard(cluster, clusterKey, index === 0);
  });
  elements.semanticBundles.innerHTML = `
    <div class="analysis-section-shell semantic-bundle-shell is-first">
      <section class="analysis-section semantic-bundle-section is-primary">
        <div class="analysis-section-head">
          <div>
            ${trendLead}
          </div>
          <div class="analysis-section-metrics">
            <span class="analysis-metric-pill" aria-label="${coveredRows}개 공고">
              <span class="analysis-metric-pill-core">
                <strong aria-hidden="true">${renderAnimatedMetricText(coveredRows, "is-number")}</strong>
                <em aria-hidden="true">${renderAnimatedMetricText("공고", "is-label")}</em>
              </span>
            </span>
            <span class="analysis-metric-pill" aria-label="${clusters.length}개 묶음">
              <span class="analysis-metric-pill-core">
                <strong aria-hidden="true">${renderAnimatedMetricText(clusters.length, "is-number")}</strong>
                <em aria-hidden="true">${renderAnimatedMetricText("묶음", "is-label")}</em>
              </span>
            </span>
          </div>
        </div>
        <div class="semantic-bundle-grid">
          ${clusterCards.join("")}
        </div>
      </section>
      <div class="semantic-bundle-divider" aria-hidden="true"></div>
    </div>
  `;
}

function renderFieldSections() {
  const rows = currentRows();
  if (!rows.length) {
    state.clusterMap = new Map();
    state.activeClusterKey = null;
    elements.fieldSections.innerHTML = `<div class="empty-state">조건에 맞는 공고가 없습니다.</div>`;
    return;
  }

  state.clusterMap = new Map();
  elements.fieldSections.innerHTML = FIELD_SECTIONS.map((section, index) =>
    renderFieldSection(section, rows, index, FIELD_SECTIONS.length),
  ).join("");
}

function collectDrawerKeywords(row, cluster) {
  const merged = [
    ...(row.highlightKeywords || []),
    ...((row.signalFacets && row.signalFacets.keyword) || []),
    ...((row.structuredSignals && row.structuredSignals.problemSignals) || []),
    ...((row.structuredSignals && row.structuredSignals.dataSignals) || []),
    ...(row.skills || []),
    ...(cluster.keywords || []),
  ];
  const seen = new Set();
  return merged.filter((term) => {
    const key = canonical(term);
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, 4);
}

function buildDrawerSummary(row) {
  const source =
    row.summary
    || row.companyHeadline
    || row.groupSummary
    || row.rawSummary
    || row.detailBody
    || "";
  const cleaned = String(source || "").replace(/\s+/g, " ").trim();
  if (!cleaned) {
    return "요약 정보가 아직 정리되지 않았습니다.";
  }
  return cleaned.length > 150 ? `${cleaned.slice(0, 150).trim()}...` : cleaned;
}

function buildCompanyHoverCopy(row) {
  const company = row.company || "이 회사";
  const headline = String(row.companyHeadline || "").trim();
  const keywords = (row.companyKeywords || []).filter(Boolean).slice(0, 3);
  const summary = String(row.companyReason || "").trim();

  const opening = headline
    ? `${company}는 지금 채용 신호상 ${headline} 축이 가장 강하게 읽히는 회사입니다.`
    : `${company}는 현재 채용 공고 흐름에서 반복 신호가 비교적 또렷한 회사입니다.`;

  const detail = summary
    ? ` ${summary}`
    : keywords.length
      ? ` ${keywords.join(" · ")} 관련 표현이 반복적으로 보입니다.`
      : "";

  return `${opening}${detail}`.trim();
}

function clusterRows(cluster) {
  const postingIds = new Set(cluster?.postingIds || []);
  return currentRows()
    .filter((row) => postingIds.has(row.id))
    .sort(
      (left, right) =>
        Number(right.active) - Number(left.active)
        || String(left.company || "").localeCompare(String(right.company || "")),
    );
}

function renderDrawerPosting(row, cluster) {
  const roleLabel = row.roleGroup || row.role || "기타";
  const keywords = collectDrawerKeywords(row, cluster);
  const summary = buildDrawerSummary(row);
  const companyBrief = buildCompanyHoverCopy(row);
  return `
    <article class="drawer-posting-card ${cluster.tone}">
      <div class="drawer-posting-top">
        <div class="drawer-posting-copy">
          <button
            type="button"
            class="drawer-posting-company company-hover-trigger"
            data-job-id="${escapeHtml(row.id || "")}"
            data-company-name="${escapeHtml(row.company || "회사 미상")}"
            data-company-brief="${escapeHtml(companyBrief)}"
          ><span class="drawer-posting-company-label">${escapeHtml(row.company || "회사 미상")}</span><span class="drawer-posting-company-orbit" aria-hidden="true"><span class="company-orbit-rail"></span><span class="company-orbit-stars"><span class="company-orbit-star star-a"></span><span class="company-orbit-star star-b"></span><span class="company-orbit-star star-c"></span></span></span></button>
          <h4
            class="drawer-posting-title posting-hover-trigger"
            tabindex="0"
            data-job-id="${escapeHtml(row.id || "")}"
            data-hover-label="${escapeHtml(row.title || "공고명 없음")}"
            data-company-name="${escapeHtml(row.company || "회사 미상")}"
            data-company-brief="${escapeHtml(summary)}"
          >${escapeHtml(row.title || "공고명 없음")}</h4>
        </div>
        ${
          row.jobUrl
            ? `<a class="link-arrow-button drawer-posting-link" href="${escapeHtml(row.jobUrl)}" target="_blank" rel="noreferrer noopener" aria-label="${escapeHtml(`${row.company || ""} ${row.title || ""}`.trim())} 공고 열기"></a>`
            : ""
        }
      </div>
      <div class="chip-row drawer-posting-meta">
        <span class="chip ${row.active ? "success" : ""}">${row.active ? "활성" : "마감"}</span>
        <span class="chip">${escapeHtml(roleLabel)}</span>
        ${row.focusLabel ? `<span class="chip primary">${escapeHtml(row.focusLabel)}</span>` : ""}
      </div>
      <p class="drawer-posting-summary">${escapeHtml(summary)}</p>
      ${
        keywords.length
          ? `<div class="drawer-posting-keywords">${keywords
              .map((keyword) => `<span class="keyword-chip ${cluster.tone}">${escapeHtml(keyword)}</span>`)
              .join("")}</div>`
          : ""
      }
    </article>
  `;
}

function stopCompanyHoverTyping() {
  if (state.companyHoverTimer) {
    window.clearInterval(state.companyHoverTimer);
    state.companyHoverTimer = 0;
  }
}

function startCompanyHoverLoadingSequence() {
  if (!elements.companyHoverLoadingCopy) return;
  const steps = [
    "공고 신호를 읽고 있어요",
    "역할과 맥락을 정리하고 있어요",
    "핵심 포인트를 조용히 묶고 있어요",
  ];
  let index = 0;
  elements.companyHoverLoadingCopy.textContent = steps[0];
  stopCompanyHoverTyping();
  state.companyHoverTimer = window.setInterval(() => {
    index = (index + 1) % steps.length;
    if (elements.companyHoverLoadingCopy) {
      elements.companyHoverLoadingCopy.textContent = steps[index];
    }
  }, 680);
}

function setCompanyHoverLoading(isLoading) {
  if (!elements.companyHoverPopover || !elements.companyHoverLoading || !elements.companyHoverBody) return;
  elements.companyHoverPopover.classList.toggle("is-loading", Boolean(isLoading));
  elements.companyHoverLoading.setAttribute("aria-hidden", isLoading ? "false" : "true");
  elements.companyHoverBody.setAttribute("aria-hidden", isLoading ? "true" : "false");
  if (elements.companyHoverLoadingCopy && !isLoading) {
    elements.companyHoverLoadingCopy.textContent = "";
  }
}

function hideCompanyHoverPopover() {
  stopCompanyHoverTyping();
  state.companyHoverRequestId += 1;
  state.companyHoverTarget = null;
  if (
    !elements.companyHoverPopover ||
    !elements.companyHoverLabel ||
    !elements.companyHoverHeadline ||
    !elements.companyHoverParagraphs ||
    !elements.companyHoverSignals
  ) {
    return;
  }
  setCompanyHoverLoading(false);
  elements.companyHoverPopover.classList.remove("is-open");
  elements.companyHoverPopover.setAttribute("aria-hidden", "true");
  elements.companyHoverLabel.textContent = "";
  elements.companyHoverHeadline.textContent = "";
  elements.companyHoverParagraphs.innerHTML = "";
  elements.companyHoverSignals.innerHTML = "";
}

function placeCompanyHoverPopover(trigger) {
  if (!elements.companyHoverPopover) return;
  const rect = trigger.getBoundingClientRect();
  const popoverRect = elements.companyHoverPopover.getBoundingClientRect();
  const gap = 14;
  let left = rect.right + gap;
  let top = rect.top + rect.height / 2 - popoverRect.height / 2;

  if (left + popoverRect.width > window.innerWidth - 16) {
    left = rect.left - popoverRect.width - gap;
  }
  if (left < 16) {
    left = Math.max(16, Math.min(window.innerWidth - popoverRect.width - 16, rect.left));
    top = rect.bottom + 12;
  }

  top = Math.max(16, Math.min(window.innerHeight - popoverRect.height - 16, top));
  elements.companyHoverPopover.style.left = `${left}px`;
  elements.companyHoverPopover.style.top = `${top}px`;
}

function buildCompanyFallbackCard(companyName, fallback) {
  const summary = fallback || `${companyName} 공고의 핵심 설명을 불러오는 중입니다.`;
  return {
    headline: "공고 해석을 준비 중입니다",
    paragraphs: [summary],
    signals: [],
  };
}

function splitInsightParagraphs(value, limit = 3) {
  const source = String(value || "").replace(/\r/g, "\n").trim();
  if (!source) return [];

  const directParagraphs = source
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean);
  if (directParagraphs.length > 1) {
    return directParagraphs.slice(0, limit);
  }

  const sentences = source.match(/[^.!?]+[.!?]?/g) || [source];
  const paragraphs = [];
  let chunk = "";
  for (const sentence of sentences.map((item) => item.trim()).filter(Boolean)) {
    const next = chunk ? `${chunk} ${sentence}` : sentence;
    if (next.length > 92 && chunk) {
      paragraphs.push(chunk);
      chunk = sentence;
    } else {
      chunk = next;
    }
  }
  if (chunk) {
    paragraphs.push(chunk);
  }
  return paragraphs.slice(0, limit);
}

function normalizeCompanyInsightCard(payload, companyName, fallback) {
  if (!payload || typeof payload !== "object") {
    return buildCompanyFallbackCard(companyName, fallback);
  }

  const source = payload.card && typeof payload.card === "object" ? payload.card : payload;
  const headline = String(source.headline || "").trim();
  const summary = String(source.summary || source.insight || fallback || "").trim();
  const paragraphs = Array.isArray(source.paragraphs)
    ? source.paragraphs.map((item) => String(item || "").trim()).filter(Boolean).slice(0, 3)
    : splitInsightParagraphs(summary, 3);
  const signals = Array.isArray(source.signals)
    ? source.signals.map((item) => String(item || "").trim()).filter(Boolean).slice(0, 3)
    : [];

  return {
    headline: headline || "이 공고의 핵심 포인트",
    paragraphs: paragraphs.length
      ? paragraphs
      : splitInsightParagraphs(
          fallback || `${companyName} 공고의 핵심 설명을 아직 충분히 불러오지 못했습니다.`,
          2,
        ),
    signals,
  };
}

function formatCompanyHoverSignal(signal) {
  const text = String(signal || "").trim();
  if (!text) return "";
  const separatorIndex = text.indexOf(":");
  if (separatorIndex <= 0) {
    return escapeHtml(text);
  }
  const label = text.slice(0, separatorIndex).trim();
  const content = text.slice(separatorIndex + 1).trim();
  if (!label || !content) {
    return escapeHtml(text);
  }
  return `<strong>${escapeHtml(label)}</strong> ${escapeHtml(content)}`;
}

function renderCompanyHoverCard(card, trigger, requestId) {
  stopCompanyHoverTyping();
  if (
    !elements.companyHoverHeadline ||
    !elements.companyHoverParagraphs ||
    !elements.companyHoverSignals
  ) {
    return;
  }

  elements.companyHoverHeadline.textContent = card.headline || "이 공고의 핵심 포인트";
  elements.companyHoverParagraphs.innerHTML = (card.paragraphs || [])
    .map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`)
    .join("");
  elements.companyHoverSignals.innerHTML = (card.signals || [])
    .map((signal) => `<li>${formatCompanyHoverSignal(signal)}</li>`)
    .join("");

  if (state.companyHoverRequestId === requestId && state.companyHoverTarget === trigger) {
    placeCompanyHoverPopover(trigger);
  }
}

async function fetchCompanyHoverInsight(jobId, fallback) {
  if (!jobId) {
    return { card: fallback, cached: false, stale: true };
  }

  if (state.companyInsightCache.has(jobId)) {
    return { card: state.companyInsightCache.get(jobId), cached: true, stale: false, localCache: true };
  }

  try {
    const result = await postJson("/api/company-insight", {
      jobId,
      config: readCompanyInsightConfig(),
    });
    const companyName = String(result.company || "").trim();
    const card = normalizeCompanyInsightCard(result, companyName, fallback);
    if (card && !result.stale) {
      state.companyInsightCache.set(jobId, card);
    }
    return { ...result, card };
  } catch (error) {
    return { card: fallback, cached: false, stale: true, error: error.message };
  }
}

async function showCompanyHoverPopover(trigger) {
  if (
    !trigger ||
    !elements.companyHoverPopover ||
    !elements.companyHoverLabel ||
    !elements.companyHoverHeadline ||
    !elements.companyHoverParagraphs ||
    !elements.companyHoverSignals
  ) {
    return;
  }

  const jobId = trigger.dataset.jobId || "";
  const companyName = trigger.dataset.hoverLabel || trigger.dataset.companyName || trigger.textContent || "회사";
  const companyBrief = trigger.dataset.companyBrief || "이 공고의 핵심 신호를 불러오는 중입니다.";
  const fallbackCard = buildCompanyFallbackCard(companyName, companyBrief);
  const requestId = state.companyHoverRequestId + 1;
  const minimumReadDelay = 820;

  stopCompanyHoverTyping();
  state.companyHoverRequestId = requestId;
  state.companyHoverTarget = trigger;
  elements.companyHoverLabel.textContent = companyName;
  elements.companyHoverHeadline.textContent = "";
  elements.companyHoverParagraphs.innerHTML = "";
  elements.companyHoverSignals.innerHTML = "";
  setCompanyHoverLoading(true);
  startCompanyHoverLoadingSequence();
  elements.companyHoverPopover.classList.add("is-open");
  elements.companyHoverPopover.setAttribute("aria-hidden", "false");
  placeCompanyHoverPopover(trigger);

  const [insightResult] = await Promise.all([
    fetchCompanyHoverInsight(jobId, fallbackCard),
    new Promise((resolve) => window.setTimeout(resolve, minimumReadDelay)),
  ]);
  if (state.companyHoverRequestId !== requestId || state.companyHoverTarget !== trigger) return;

  setCompanyHoverLoading(false);
  stopCompanyHoverTyping();
  renderCompanyHoverCard(
    normalizeCompanyInsightCard(insightResult.card, companyName, companyBrief),
    trigger,
    requestId,
  );
}

function closeClusterDrawer() {
  if (!state.activeClusterKey && !state.drawerClusterKey) return;
  if (state.drawerCloseTimer) {
    window.clearTimeout(state.drawerCloseTimer);
    state.drawerCloseTimer = 0;
  }
  state.activeClusterKey = null;
  state.drawerIsClosing = true;
  hideCompanyHoverPopover();
  renderFieldSections();
  renderSemanticBundles();
  renderClusterDrawer();
  scheduleClusterCardHeightSync();

  state.drawerCloseTimer = window.setTimeout(() => {
    state.drawerCloseTimer = 0;
    state.drawerIsClosing = false;
    state.drawerClusterKey = null;
    renderClusterDrawer();
  }, 360);
}

function openClusterDrawer(clusterKey) {
  if (!state.clusterMap.has(clusterKey)) return;
  if (state.activeClusterKey === clusterKey) {
    closeClusterDrawer();
    return;
  }
  if (state.drawerCloseTimer) {
    window.clearTimeout(state.drawerCloseTimer);
    state.drawerCloseTimer = 0;
  }
  state.drawerIsClosing = false;
  state.activeClusterKey = clusterKey;
  state.drawerClusterKey = clusterKey;
  hideCompanyHoverPopover();
  renderFieldSections();
  renderSemanticBundles();
  renderClusterDrawer();
  scheduleClusterCardHeightSync();
}

function renderClusterDrawer() {
  if (!elements.clusterDrawerShell || !elements.clusterDrawerPanel || !elements.clusterDrawerContent) {
    return;
  }

  const drawerClusterKey = state.activeClusterKey || state.drawerClusterKey;
  const cluster = drawerClusterKey ? state.clusterMap.get(drawerClusterKey) : null;
  if (!cluster) {
    elements.clusterDrawerShell.classList.remove("is-open");
    elements.clusterDrawerShell.classList.remove("is-closing");
    elements.clusterDrawerShell.setAttribute("aria-hidden", "true");
    elements.clusterDrawerPanel.className = "cluster-drawer-panel";
    elements.clusterDrawerContent.innerHTML = "";
    return;
  }

  const rows = clusterRows(cluster);
  const companyCount = new Set(rows.map((row) => row.company).filter(Boolean)).size;
  const hoverHint = hasLiveCompanyInsightConfig()
    ? "회사명이나 공고 제목 위에 마우스를 올리면 AI가 공고 맥락을 다시 요약합니다."
    : "회사명이나 공고 제목 위에 마우스를 올리면 저장된 요약과 공고 신호를 바로 확인할 수 있습니다.";
  elements.clusterDrawerShell.classList.toggle("is-open", Boolean(state.activeClusterKey));
  elements.clusterDrawerShell.classList.toggle("is-closing", state.drawerIsClosing);
  elements.clusterDrawerShell.setAttribute("aria-hidden", state.activeClusterKey ? "false" : "true");
  elements.clusterDrawerPanel.className = `cluster-drawer-panel ${cluster.tone}`;
  elements.clusterDrawerContent.innerHTML = `
    <div class="cluster-drawer-header">
      <div class="cluster-drawer-header-row">
        <div>
          <p class="cluster-drawer-kicker">${escapeHtml(cluster.sectionLabel)}</p>
          <h3 class="cluster-drawer-title">${escapeHtml(cluster.label)}</h3>
        </div>
      </div>
      <p class="cluster-drawer-copy">${escapeHtml(cluster.description || "")}</p>
      <div class="cluster-drawer-meta">
        <span>${rows.length}개 공고</span>
        <span>${companyCount}개 기업</span>
      </div>
      ${
        cluster.keywords?.length
          ? `<div class="cluster-drawer-keywords">${cluster.keywords
              .slice(0, 5)
              .map((keyword) => `<span class="keyword-chip ${cluster.tone}">${escapeHtml(keyword)}</span>`)
              .join("")}</div>`
          : ""
      }
      <div class="cluster-drawer-hint">
        <p data-hint="${escapeHtml(hoverHint)}">${escapeHtml(hoverHint)}</p>
      </div>
    </div>
    <div class="cluster-drawer-list">
      ${
        rows.length
          ? rows.map((row) => renderDrawerPosting(row, cluster)).join("")
          : `<div class="cluster-drawer-empty">현재 필터에서 이 군집에 속한 공고가 없습니다.</div>`
      }
    </div>
  `;
}

let clusterHeightFrame = 0;

function syncClusterCardHeights() {
  const cards = Array.from(document.querySelectorAll(".field-sections .field-cluster-card"));
  if (!cards.length) {
    return;
  }

  cards.forEach((card) => {
    card.style.removeProperty("--cluster-card-height");
  });

  const maxHeight = Math.ceil(
    cards.reduce((height, card) => Math.max(height, card.getBoundingClientRect().height), 0),
  );

  cards.forEach((card) => {
    card.style.setProperty("--cluster-card-height", `${maxHeight}px`);
  });
}

function scheduleClusterCardHeightSync() {
  if (clusterHeightFrame) {
    cancelAnimationFrame(clusterHeightFrame);
  }

  clusterHeightFrame = window.requestAnimationFrame(() => {
    clusterHeightFrame = 0;
    syncClusterCardHeights();
  });
}

function renderBoard() {
  renderRoleTabs();
  renderActivityTabs();
  renderOverview();
  renderRoleResumeButton();
  renderFieldSections();
  renderSemanticBundles();
  if (state.activeClusterKey && !state.clusterMap.has(state.activeClusterKey)) {
    state.activeClusterKey = null;
  }
  renderClusterDrawer();
  renderRoleResumeOverlay();
  scheduleClusterCardHeightSync();
}

async function loadBoard(forceRefresh) {
  const suffix = forceRefresh ? "?refresh=1" : "";
  const response = await fetch(`/api/summary-board${suffix}`, { cache: "no-store" });
  state.board = normalizeBoardPayload(await response.json());
  renderBoard();
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await response.json();
  if (!response.ok || !body.ok) {
    throw new Error(body.error || "요청 실패");
  }
  return body;
}

async function runSummaries(mode) {
  const config = saveConfig();
  const batchSize = readBatchSize();

  if (mode === "all") {
    setStatus("전체 요약과 키워드를 다시 정리하는 중...");
    const result = await postJson("/api/summaries/run", {
      config,
      batchSize,
      limitJobs: state.board.overview.totalJobs,
      mode,
    });
    await loadBoard(true);
    setStatus(`전체 재정리 완료 · 처리 ${result.processed}건 · 저장 ${result.saved}건`);
    return;
  }

  setStatus("누락된 요약과 키워드를 정리하는 중...");
  let loopCount = 0;

  while (true) {
    loopCount += 1;
    const result = await postJson("/api/summaries/run", {
      config,
      batchSize,
      limitJobs: batchSize,
      mode: "missing",
    });

    await loadBoard(true);
    setStatus(
      `배치 ${loopCount} 완료 · 처리 ${result.processed}건 · 저장 ${result.saved}건 · 남은 ${result.overview.missingSummaries}건`,
    );

    if (result.overview.missingSummaries === 0 || result.processed === 0) {
      break;
    }
  }

  setStatus("누락된 요약 정리가 끝났습니다.");
}

function bindEvents() {
  elements.saveConfig.addEventListener("click", () => {
    saveConfig();
  });

  elements.openRoleResumeGuides?.addEventListener("click", async () => {
    await openRoleResumeOverlay();
  });

  elements.syncSheet.addEventListener("click", async () => {
    elements.syncSheet.classList.add("is-loading");
    elements.syncSheet.disabled = true;
    elements.syncSheet.setAttribute("aria-busy", "true");
    try {
      setStatus("시트의 최신 검수 결과를 읽고 화면 데이터를 갱신하는 중...");
      const result = await postJson("/api/source/sync", {
        autoEnrich: false,
        config: {},
        batchSize: readBatchSize(),
        promptProfile: "field_aware_v3",
      });
      await loadBoard(true);
      const delta = result.delta || {};
      const summaries = result.summaries || {};
      const parts = [
        `데이터 반영 완료`,
        `${result.rowCount}건 확인`,
        `신규 ${delta.added || 0}건`,
        `변경 ${delta.changed || 0}건`,
      ];

      if (summaries.enabled) {
        if (summaries.ok) {
          parts.push(`모델 보정 ${summaries.saved || 0}건 반영`);
        } else {
          parts.push(`모델 보정 실패`);
        }
      }

      if (summaries.pruned) {
        parts.push(`제거 ${summaries.pruned}건 정리`);
      }

      setStatus(parts.join(" · "));
    } catch (error) {
      setStatus(error.message);
    } finally {
      elements.syncSheet.classList.remove("is-loading");
      elements.syncSheet.disabled = false;
      elements.syncSheet.setAttribute("aria-busy", "false");
    }
  });

  elements.runMissing.addEventListener("click", async () => {
    try {
      requireConfig();
      await runSummaries("missing");
    } catch (error) {
      setStatus(error.message);
    }
  });

  elements.runAll.addEventListener("click", async () => {
    try {
      requireConfig();
      await runSummaries("all");
    } catch (error) {
      setStatus(error.message);
    }
  });

  elements.refreshBoard.addEventListener("click", async () => {
    try {
      setStatus("보드를 새로고침하는 중...");
      await loadBoard(true);
      setStatus("새로고침 완료");
    } catch (error) {
      setStatus(error.message);
    }
  });

  elements.roleTabs.addEventListener("click", (event) => {
    const button = event.target.closest("[data-role-filter]");
    if (!button) return;
    state.roleFilter = button.dataset.roleFilter || "전체";
    renderBoard();
  });

  elements.activityTabs.addEventListener("click", (event) => {
    const button = event.target.closest("[data-activity-filter]");
    if (!button) return;
    state.activityFilter = button.dataset.activityFilter || "all";
    renderBoard();
  });

  const handleClusterClick = (event) => {
    const card = event.target.closest("[data-cluster-key]");
    if (!card) return;
    openClusterDrawer(card.dataset.clusterKey || "");
  };

  const handleClusterKeydown = (event) => {
    const card = event.target.closest("[data-cluster-key]");
    if (!card) return;
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    openClusterDrawer(card.dataset.clusterKey || "");
  };

  elements.fieldSections.addEventListener("click", handleClusterClick);
  elements.fieldSections.addEventListener("keydown", handleClusterKeydown);
  elements.semanticBundles?.addEventListener("click", handleClusterClick);
  elements.semanticBundles?.addEventListener("keydown", handleClusterKeydown);

  elements.clusterDrawerScrim?.addEventListener("click", closeClusterDrawer);
  elements.clusterDrawerShell?.addEventListener("pointerdown", (event) => {
    if (!state.activeClusterKey) return;
    if (!(event.target instanceof Element)) return;
    if (event.target.closest("#cluster-drawer-panel")) return;
    closeClusterDrawer();
  });

  elements.roleResumeScrim?.addEventListener("click", closeRoleResumeOverlay);
  elements.roleResumeShell?.addEventListener("pointerdown", (event) => {
    if (!state.roleResumeOpen && !state.roleResumeLoading && !state.roleResumeError) return;
    if (!(event.target instanceof Element)) return;
    if (event.target.closest("#role-resume-panel")) return;
    closeRoleResumeOverlay();
  });
  elements.roleResumeContent?.addEventListener("click", (event) => {
    const closeButton = event.target.closest("[data-close-role-resume]");
    if (closeButton) {
      closeRoleResumeOverlay();
      return;
    }
    const downloadButton = event.target.closest("[data-download-role-resume-pdf]");
    if (downloadButton) {
      downloadRoleResumePdf().catch((error) => {
        state.roleResumeNotice = `PDF 저장에 실패했습니다. ${error.message}`;
        state.roleResumeNoticeTone = "error";
        state.roleResumePdfExporting = false;
        renderRoleResumeOverlay();
        setStatus(error.message);
      });
      return;
    }
    const regenerateButton = event.target.closest("[data-regenerate-role-resume]");
    if (regenerateButton) {
      regenerateRoleResumeOverlay();
    }
  });

  elements.clusterDrawerContent?.addEventListener("mouseover", (event) => {
    const trigger = event.target.closest(".company-hover-trigger, .posting-hover-trigger");
    if (!trigger || trigger === state.companyHoverTarget) return;
    showCompanyHoverPopover(trigger);
  });

  elements.clusterDrawerContent?.addEventListener("mouseout", (event) => {
    const trigger = event.target.closest(".company-hover-trigger, .posting-hover-trigger");
    if (!trigger) return;
    const related = event.relatedTarget;
    if (related && trigger.contains(related)) return;
    hideCompanyHoverPopover();
  });

  elements.clusterDrawerContent?.addEventListener("focusin", (event) => {
    const trigger = event.target.closest(".company-hover-trigger, .posting-hover-trigger");
    if (!trigger) return;
    showCompanyHoverPopover(trigger);
  });

  elements.clusterDrawerContent?.addEventListener("focusout", (event) => {
    const trigger = event.target.closest(".company-hover-trigger, .posting-hover-trigger");
    if (!trigger) return;
    const related = event.relatedTarget;
    if (related && trigger.contains(related)) return;
    hideCompanyHoverPopover();
  });

  elements.clusterDrawerContent?.addEventListener("scroll", hideCompanyHoverPopover, true);

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      if (state.roleResumeOpen || state.roleResumeLoading || state.roleResumeError) {
        closeRoleResumeOverlay();
        return;
      }
      closeClusterDrawer();
    }
  });

  window.addEventListener("resize", () => {
    scheduleClusterCardHeightSync();
    if (state.companyHoverTarget) {
      placeCompanyHoverPopover(state.companyHoverTarget);
    }
  });
}

async function start() {
  writeConfig(loadSavedConfig());
  bindEvents();
  await loadBoard(false);
  setStatus("5개 분석 섹션 준비 완료");
  finishSiteIntro();
}

start().catch((error) => {
  console.error(error);
  setStatus(`초기 로드 실패: ${error.message}`);
  elements.fieldSections.innerHTML = `<div class="empty-state">데이터를 불러오지 못했습니다.</div>`;
  finishSiteIntro(true);
});
