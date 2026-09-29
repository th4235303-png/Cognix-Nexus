export type SourceStatus =
  | 'new'
  | 'processing'
  | 'needs_review'
  | 'approved'
  | 'delivered'
  | 'failed'
  | 'outdated';

export type SourceType = 'article' | 'report' | 'paper' | 'video' | 'podcast' | 'dataset';
export type TrustLevel = 'verified' | 'high' | 'medium' | 'low' | 'unverified';
export type Priority = 'critical' | 'high' | 'normal' | 'low';

export interface Source {
  id: string;
  title: string;
  type: SourceType;
  publisher: string;
  author: string;
  topic: string;
  status: SourceStatus;
  trust: TrustLevel;
  priority: Priority;
  url: string;
  publishedDate: string;
  retrievedDate: string;
  lastProcessed: string;
  lastReviewed: string | null;
  freshness: string;
  addedDate: string;
  version: string;
  contentHash: string;
  summary: string;
  keyPoints: string[];
  tags: string[];
  claims: Claim[];
  relatedSourceIds: string[];
  duplicate?: boolean;
}

export interface Claim {
  id: string;
  text: string;
  excerpt: string;
  location: string;
  confidence: number;
  verification: 'verified' | 'pending' | 'conflicted' | 'unsupported';
}

export interface ProcessingTask {
  id: string;
  sourceId: string;
  sourceTitle: string;
  sourceType: SourceType;
  taskType: 'extract' | 'clean' | 'summarize' | 'classify' | 'full';
  stage:
    | 'queued'
    | 'extracting'
    | 'cleaning'
    | 'summarizing'
    | 'classifying'
    | 'needs_review'
    | 'completed'
    | 'failed';
  progress: number;
  startedTime: string;
  duration: string;
  retryCount: number;
  status: 'running' | 'queued' | 'paused' | 'completed' | 'failed';
  error?: string;
  retryHistory: { time: string; result: string }[];
}

export interface DeliveryEvent {
  id: string;
  sourceId: string;
  sourceTitle: string;
  destination: 'Logixa Flow' | 'Aether Bridge' | 'Archive';
  version: string;
  sentTime: string;
  acknowledgedTime: string | null;
  attemptCount: number;
  status:
    | 'queued'
    | 'sending'
    | 'delivered'
    | 'acknowledged'
    | 'retry_pending'
    | 'failed'
    | 'duplicate_ignored';
  error?: string;
  lastSuccessfulDelivery?: string;
}

export interface ActivityEntry {
  id: string;
  user: string;
  avatar: string;
  action: string;
  target: string;
  previousState: string;
  newState: string;
  timestamp: string;
  requestId: string;
}

export interface Collection {
  id: string;
  name: string;
  description: string;
  sourceCount: number;
  color: string;
  updatedAt: string;
}

export interface TagTopic {
  id: string;
  label: string;
  type: 'tag' | 'topic';
  count: number;
}

export interface Notification {
  id: string;
  title: string;
  description: string;
  type: 'info' | 'success' | 'warning' | 'error';
  time: string;
  read: boolean;
  link: string;
}

export const sources: Source[] = [
  {
    id: 'SRC-0481',
    title: 'Transformer Architecture: Attention Mechanisms Revisited',
    type: 'paper',
    publisher: 'arXiv',
    author: 'Dr. Elena Vasquez',
    topic: 'Machine Learning',
    status: 'needs_review',
    trust: 'high',
    priority: 'high',
    url: 'https://arxiv.org/abs/2024.0481',
    publishedDate: '2026-08-14',
    retrievedDate: '2026-08-28',
    lastProcessed: '2026-08-28T09:14:00Z',
    lastReviewed: null,
    freshness: '2h ago',
    addedDate: '2026-08-28',
    version: 'v2.1',
    contentHash: '0x7a3f9c2e8b1d4f6a',
    summary:
      'A comprehensive re-examination of attention mechanisms in transformer architectures, proposing a sparse-attention variant that reduces computational complexity from O(n²) to O(n log n) while preserving model performance on benchmark tasks.',
    keyPoints: [
      'Sparse attention reduces complexity to O(n log n)',
      'Performance preserved across GLUE, SQuAD, and SuperGLUE benchmarks',
      'Memory footprint reduced by 38% on sequences over 4K tokens',
      'Compatible with existing pre-trained checkpoint fine-tuning',
    ],
    tags: ['transformers', 'attention', 'efficiency', 'NLP'],
    claims: [
      {
        id: 'CLM-001',
        text: 'Sparse attention achieves equivalent performance to full attention on GLUE benchmark.',
        excerpt:
          'Our sparse variant matches full-attention accuracy within 0.3% on all GLUE tasks while reducing peak memory by 38%.',
        location: 'Section 4.2, Table 3',
        confidence: 87,
        verification: 'verified',
      },
      {
        id: 'CLM-002',
        text: 'Memory reduction scales linearly with sequence length beyond 4K tokens.',
        excerpt:
          'For sequences exceeding 4096 tokens, memory consumption follows a linear rather than quadratic curve.',
        location: 'Section 5.1, Figure 4',
        confidence: 72,
        verification: 'pending',
      },
      {
        id: 'CLM-003',
        text: 'The method is compatible with existing pre-trained checkpoints.',
        excerpt:
          'Fine-tuning from existing checkpoints requires no architectural retraining, only adapter adjustment.',
        location: 'Section 6, Appendix C',
        confidence: 64,
        verification: 'conflicted',
      },
    ],
    relatedSourceIds: ['SRC-0479', 'SRC-0462'],
  },
  {
    id: 'SRC-0479',
    title: 'Efficient Inference for Large Language Models: A Survey',
    type: 'report',
    publisher: 'DeepMind Research',
    author: 'Marcus Chen',
    topic: 'AI Infrastructure',
    status: 'processing',
    trust: 'verified',
    priority: 'normal',
    url: 'https://research.deepmind.com/efficient-inference-2026',
    publishedDate: '2026-08-20',
    retrievedDate: '2026-08-30',
    lastProcessed: '2026-08-30T07:00:00Z',
    lastReviewed: null,
    freshness: '12m ago',
    addedDate: '2026-08-30',
    version: 'v1.0',
    contentHash: '0x9b2e4a8f1c7d3e5b',
    summary:
      'A survey of inference optimization techniques including quantization, distillation, and speculative decoding across production-scale LLM deployments.',
    keyPoints: [
      'INT4 quantization preserves 97% of FP16 performance',
      'Speculative decoding yields 2.3x throughput improvement',
      'Distillation reduces model size by 60% with minimal loss',
    ],
    tags: ['inference', 'optimization', 'quantization', 'LLM'],
    claims: [],
    relatedSourceIds: ['SRC-0481'],
  },
  {
    id: 'SRC-0462',
    title: 'Multimodal Reasoning Benchmarks: State of the Art 2026',
    type: 'paper',
    publisher: 'NeurIPS',
    author: 'Priya Anand',
    topic: 'Multimodal AI',
    status: 'approved',
    trust: 'verified',
    priority: 'normal',
    url: 'https://neurips.cc/2026/multimodal-benchmarks',
    publishedDate: '2026-07-30',
    retrievedDate: '2026-08-15',
    lastProcessed: '2026-08-15T14:22:00Z',
    lastReviewed: '2026-08-16',
    freshness: '15d ago',
    addedDate: '2026-08-15',
    version: 'v1.3',
    contentHash: '0x3c1d9f7a2e8b4c6d',
    summary:
      'A unified evaluation framework for multimodal reasoning spanning vision-language, audio-language, and cross-modal tasks with standardized metrics.',
    keyPoints: [
      'Unified benchmark across 5 modalities',
      'Standardized evaluation protocol adopted by 12 labs',
      'Identifies reasoning gaps in current frontier models',
    ],
    tags: ['multimodal', 'benchmarks', 'evaluation'],
    claims: [],
    relatedSourceIds: ['SRC-0481'],
  },
  {
    id: 'SRC-0455',
    title: 'The Economic Impact of Generative AI on Knowledge Work',
    type: 'report',
    publisher: 'McKinsey Global Institute',
    author: 'James Whitfield',
    topic: 'AI Economics',
    status: 'delivered',
    trust: 'verified',
    priority: 'normal',
    url: 'https://mckinsey.com/gen-ai-economic-impact-2026',
    publishedDate: '2026-08-05',
    retrievedDate: '2026-08-10',
    lastProcessed: '2026-08-10T11:30:00Z',
    lastReviewed: '2026-08-11',
    freshness: '21d ago',
    addedDate: '2026-08-10',
    version: 'v1.1',
    contentHash: '0x5e2a8c4b1d7f3a9c',
    summary:
      'Analysis of generative AI adoption across knowledge-work sectors, estimating $4.4T in annual productivity gains by 2030.',
    keyPoints: [
      'Productivity gains concentrated in legal, finance, and software',
      'Adoption barriers remain in regulated industries',
      'Workforce transition requires 18-24 month reskilling window',
    ],
    tags: ['economics', 'generative-ai', 'productivity'],
    claims: [],
    relatedSourceIds: [],
  },
  {
    id: 'SRC-0450',
    title: 'Retrieval-Augmented Generation: Production Patterns',
    type: 'article',
    publisher: 'The Gradient',
    author: 'Sofia Nakamura',
    topic: 'RAG Systems',
    status: 'new',
    trust: 'medium',
    priority: 'high',
    url: 'https://thegradient.com/rag-production-patterns',
    publishedDate: '2026-08-29',
    retrievedDate: '2026-08-31',
    lastProcessed: '2026-08-31T08:00:00Z',
    lastReviewed: null,
    freshness: '4h ago',
    addedDate: '2026-08-31',
    version: 'v1.0',
    contentHash: '0x1f7c3a9d2e6b4c8a',
    summary: '',
    keyPoints: [],
    tags: ['RAG', 'production', 'patterns'],
    claims: [],
    relatedSourceIds: [],
  },
  {
    id: 'SRC-0448',
    title: 'AI Safety Alignment: Constitutional AI Methods',
    type: 'paper',
    publisher: 'Anthropic',
    author: 'Dr. Raj Patel',
    topic: 'AI Safety',
    status: 'needs_review',
    trust: 'high',
    priority: 'critical',
    url: 'https://anthropic.com/constitutional-ai-2026',
    publishedDate: '2026-08-22',
    retrievedDate: '2026-08-29',
    lastProcessed: '2026-08-29T16:45:00Z',
    lastReviewed: null,
    freshness: '2d ago',
    addedDate: '2026-08-29',
    version: 'v2.0',
    contentHash: '0x8a4e2c7b1d9f3a5e',
    summary:
      'Constitutional AI methods for aligning language models using principled feedback, reducing harmful outputs by 73% in adversarial evaluations.',
    keyPoints: [
      'Principled feedback reduces harmful outputs by 73%',
      'Self-critique loop improves alignment over 3 iterations',
      'Method generalizes across model scales from 7B to 70B',
    ],
    tags: ['safety', 'alignment', 'constitutional-ai'],
    claims: [
      {
        id: 'CLM-010',
        text: 'Constitutional AI reduces harmful outputs by 73% in adversarial evaluations.',
        excerpt:
          'Across 12 adversarial benchmark suites, harmful output rates dropped from 8.1% to 2.2%.',
        location: 'Section 3, Table 1',
        confidence: 91,
        verification: 'verified',
      },
      {
        id: 'CLM-011',
        text: 'The self-critique method generalizes across model scales.',
        excerpt:
          'Benefits were observed consistently from 7B to 70B parameter models.',
        location: 'Section 4.3',
        confidence: 78,
        verification: 'pending',
      },
    ],
    relatedSourceIds: [],
  },
  {
    id: 'SRC-0441',
    title: 'Edge AI: On-Device Inference Optimization',
    type: 'article',
    publisher: 'IEEE Spectrum',
    author: 'Linda Park',
    topic: 'Edge AI',
    status: 'failed',
    trust: 'unverified',
    priority: 'low',
    url: 'https://spectrum.ieee.org/edge-ai-optimization',
    publishedDate: '2026-08-18',
    retrievedDate: '2026-08-25',
    lastProcessed: '2026-08-25T10:00:00Z',
    lastReviewed: null,
    freshness: '6d ago',
    addedDate: '2026-08-25',
    version: 'v1.0',
    contentHash: '0x2b9f4a7c1e3d5b8a',
    summary: '',
    keyPoints: [],
    tags: ['edge-ai', 'optimization', 'on-device'],
    claims: [],
    relatedSourceIds: [],
  },
  {
    id: 'SRC-0438',
    title: 'Dataset Card Transparency Standards v2',
    type: 'dataset',
    publisher: 'Hugging Face',
    author: 'Tomás Rivera',
    topic: 'Data Governance',
    status: 'outdated',
    trust: 'high',
    priority: 'normal',
    url: 'https://huggingface.co/dataset-cards-v2',
    publishedDate: '2026-06-10',
    retrievedDate: '2026-07-01',
    lastProcessed: '2026-07-01T09:00:00Z',
    lastReviewed: '2026-07-05',
    freshness: '2mo ago',
    addedDate: '2026-07-01',
    version: 'v1.0',
    contentHash: '0x6d3a8c1f4b7e2c9d',
    summary:
      'Updated transparency standards for dataset documentation including provenance, licensing, and bias reporting fields.',
    keyPoints: [
      'Mandatory provenance tracking fields',
      'Standardized bias reporting schema',
      'License compatibility matrix',
    ],
    tags: ['datasets', 'governance', 'transparency'],
    claims: [],
    relatedSourceIds: [],
  },
  {
    id: 'SRC-0435',
    title: 'Neuro-Symbolic Reasoning: Bridging Pattern and Logic',
    type: 'paper',
    publisher: 'MIT CSAIL',
    author: 'Dr. Amara Okafor',
    topic: 'Neuro-Symbolic AI',
    status: 'approved',
    trust: 'verified',
    priority: 'normal',
    url: 'https://csail.mit.edu/neuro-symbolic-2026',
    publishedDate: '2026-08-12',
    retrievedDate: '2026-08-20',
    lastProcessed: '2026-08-20T13:00:00Z',
    lastReviewed: '2026-08-21',
    freshness: '11d ago',
    addedDate: '2026-08-20',
    version: 'v1.2',
    contentHash: '0x4c7b2e9a1d5f3c8b',
    summary:
      'A hybrid architecture combining neural pattern recognition with symbolic logic reasoning, achieving state-of-the-art on compositional reasoning tasks.',
    keyPoints: [
      'Hybrid architecture outperforms pure neural on compositional tasks',
      'Symbolic layer enables verifiable reasoning chains',
      '40% improvement on CLEVR compositional benchmark',
    ],
    tags: ['neuro-symbolic', 'reasoning', 'hybrid-arch'],
    claims: [],
    relatedSourceIds: [],
  },
];

export const processingTasks: ProcessingTask[] = [
  {
    id: 'TSK-1024',
    sourceId: 'SRC-0479',
    sourceTitle: 'Efficient Inference for Large Language Models: A Survey',
    sourceType: 'report',
    taskType: 'full',
    stage: 'summarizing',
    progress: 64,
    startedTime: '12m ago',
    duration: '12m 14s',
    retryCount: 0,
    status: 'running',
    retryHistory: [],
  },
  {
    id: 'TSK-1023',
    sourceId: 'SRC-0450',
    sourceTitle: 'Retrieval-Augmented Generation: Production Patterns',
    sourceType: 'article',
    taskType: 'full',
    stage: 'extracting',
    progress: 18,
    startedTime: '4m ago',
    duration: '4m 02s',
    retryCount: 0,
    status: 'running',
    retryHistory: [],
  },
  {
    id: 'TSK-1022',
    sourceId: 'SRC-0441',
    sourceTitle: 'Edge AI: On-Device Inference Optimization',
    sourceType: 'article',
    taskType: 'clean',
    stage: 'failed',
    progress: 45,
    startedTime: '6d ago',
    duration: '8m 33s',
    retryCount: 3,
    status: 'failed',
    error:
      'Content extraction failed: source returned HTTP 403 after 3 retry attempts. The publisher may have rate limiting or paywall protection in place.',
    retryHistory: [
      { time: '6d ago', result: 'HTTP 403 — Forbidden' },
      { time: '5d ago', result: 'HTTP 403 — Forbidden' },
      { time: '4d ago', result: 'HTTP 403 — Forbidden' },
    ],
  },
  {
    id: 'TSK-1021',
    sourceId: 'SRC-0481',
    sourceTitle: 'Transformer Architecture: Attention Mechanisms Revisited',
    sourceType: 'paper',
    taskType: 'full',
    stage: 'needs_review',
    progress: 100,
    startedTime: '2h ago',
    duration: '14m 22s',
    retryCount: 0,
    status: 'completed',
    retryHistory: [],
  },
  {
    id: 'TSK-1020',
    sourceId: 'SRC-0448',
    sourceTitle: 'AI Safety Alignment: Constitutional AI Methods',
    sourceType: 'paper',
    taskType: 'full',
    stage: 'needs_review',
    progress: 100,
    startedTime: '2d ago',
    duration: '11m 08s',
    retryCount: 0,
    status: 'completed',
    retryHistory: [],
  },
  {
    id: 'TSK-1019',
    sourceId: 'SRC-0435',
    sourceTitle: 'Neuro-Symbolic Reasoning: Bridging Pattern and Logic',
    sourceType: 'paper',
    taskType: 'full',
    stage: 'completed',
    progress: 100,
    startedTime: '11d ago',
    duration: '16m 45s',
    retryCount: 0,
    status: 'completed',
    retryHistory: [],
  },
];

export const deliveryEvents: DeliveryEvent[] = [
  {
    id: 'EVT-2048',
    sourceId: 'SRC-0455',
    sourceTitle: 'The Economic Impact of Generative AI on Knowledge Work',
    destination: 'Logixa Flow',
    version: 'v1.1',
    sentTime: '2026-08-11 14:22 UTC',
    acknowledgedTime: '2026-08-11 14:23 UTC',
    attemptCount: 1,
    status: 'acknowledged',
    lastSuccessfulDelivery: '2026-08-11 14:22 UTC',
  },
  {
    id: 'EVT-2047',
    sourceId: 'SRC-0462',
    sourceTitle: 'Multimodal Reasoning Benchmarks: State of the Art 2026',
    destination: 'Logixa Flow',
    version: 'v1.3',
    sentTime: '2026-08-16 09:15 UTC',
    acknowledgedTime: '2026-08-16 09:16 UTC',
    attemptCount: 1,
    status: 'acknowledged',
    lastSuccessfulDelivery: '2026-08-16 09:15 UTC',
  },
  {
    id: 'EVT-2046',
    sourceId: 'SRC-0435',
    sourceTitle: 'Neuro-Symbolic Reasoning: Bridging Pattern and Logic',
    destination: 'Aether Bridge',
    version: 'v1.2',
    sentTime: '2026-08-21 11:00 UTC',
    acknowledgedTime: null,
    attemptCount: 2,
    status: 'retry_pending',
    error:
      'Aether Bridge acknowledged receipt but returned a schema validation warning. The payload structure does not match the expected v2 contract.',
    lastSuccessfulDelivery: '2026-08-20 10:30 UTC',
  },
  {
    id: 'EVT-2045',
    sourceId: 'SRC-0438',
    sourceTitle: 'Dataset Card Transparency Standards v2',
    destination: 'Logixa Flow',
    version: 'v1.0',
    sentTime: '2026-07-05 16:40 UTC',
    acknowledgedTime: '2026-07-05 16:41 UTC',
    attemptCount: 1,
    status: 'acknowledged',
    lastSuccessfulDelivery: '2026-07-05 16:40 UTC',
  },
  {
    id: 'EVT-2044',
    sourceId: 'SRC-0429',
    sourceTitle: 'Federated Learning Privacy Guarantees',
    destination: 'Aether Bridge',
    version: 'v1.0',
    sentTime: '2026-08-28 08:00 UTC',
    acknowledgedTime: null,
    attemptCount: 3,
    status: 'failed',
    error:
      'Connection to Aether Bridge timed out after 3 attempts. The bridge service may be temporarily unavailable or the network route may be blocked.',
    lastSuccessfulDelivery: '2026-08-20 14:00 UTC',
  },
  {
    id: 'EVT-2043',
    sourceId: 'SRC-0435',
    sourceTitle: 'Neuro-Symbolic Reasoning: Bridging Pattern and Logic',
    destination: 'Logixa Flow',
    version: 'v1.1',
    sentTime: '2026-08-20 10:30 UTC',
    acknowledgedTime: '2026-08-20 10:31 UTC',
    attemptCount: 1,
    status: 'acknowledged',
    lastSuccessfulDelivery: '2026-08-20 10:30 UTC',
  },
];

export const activityLog: ActivityEntry[] = [
  {
    id: 'ACT-9821',
    user: 'Elena Vasquez',
    avatar: 'EV',
    action: 'approved',
    target: 'SRC-0462',
    previousState: 'needs_review',
    newState: 'approved',
    timestamp: '2026-08-16 09:14:22 UTC',
    requestId: 'req_8a4c2e1f7b3d9a6c',
  },
  {
    id: 'ACT-9820',
    user: 'Marcus Chen',
    avatar: 'MC',
    action: 'delivered',
    target: 'SRC-0455',
    previousState: 'approved',
    newState: 'delivered',
    timestamp: '2026-08-11 14:22:08 UTC',
    requestId: 'req_2b9f4a7c1e3d5b8a',
  },
  {
    id: 'ACT-9819',
    user: 'System',
    avatar: 'SY',
    action: 'processed',
    target: 'SRC-0481',
    previousState: 'processing',
    newState: 'needs_review',
    timestamp: '2026-08-28 09:28:14 UTC',
    requestId: 'req_6d3a8c1f4b7e2c9d',
  },
  {
    id: 'ACT-9818',
    user: 'Priya Anand',
    avatar: 'PA',
    action: 'edited',
    target: 'SRC-0462',
    previousState: 'summary_v1',
    newState: 'summary_v2',
    timestamp: '2026-08-16 09:10:44 UTC',
    requestId: 'req_4c7b2e9a1d5f3c8b',
  },
  {
    id: 'ACT-9817',
    user: 'System',
    avatar: 'SY',
    action: 'failed',
    target: 'SRC-0441',
    previousState: 'extracting',
    newState: 'failed',
    timestamp: '2026-08-25 10:08:33 UTC',
    requestId: 'req_1f7c3a9d2e6b4c8a',
  },
  {
    id: 'ACT-9816',
    user: 'James Whitfield',
    avatar: 'JW',
    action: 'added',
    target: 'SRC-0450',
    previousState: '—',
    newState: 'new',
    timestamp: '2026-08-31 08:00:02 UTC',
    requestId: 'req_8a4e2c7b1d9f3a5e',
  },
  {
    id: 'ACT-9815',
    user: 'System',
    avatar: 'SY',
    action: 'retried',
    target: 'EVT-2044',
    previousState: 'retry_pending',
    newState: 'failed',
    timestamp: '2026-08-28 08:14:55 UTC',
    requestId: 'req_5e2a8c4b1d7f3a9c',
  },
];

export const collections: Collection[] = [
  {
    id: 'COL-01',
    name: 'Frontier Model Research',
    description: 'Latest papers on large-scale model architectures and training.',
    sourceCount: 14,
    color: 'cyan',
    updatedAt: '2h ago',
  },
  {
    id: 'COL-02',
    name: 'AI Safety & Alignment',
    description: 'Constitutional AI, RLHF, and safety evaluation methods.',
    sourceCount: 8,
    color: 'warning',
    updatedAt: '1d ago',
  },
  {
    id: 'COL-03',
    name: 'Production RAG Systems',
    description: 'Retrieval-augmented generation patterns and case studies.',
    sourceCount: 11,
    color: 'success',
    updatedAt: '4h ago',
  },
  {
    id: 'COL-04',
    name: 'Economic Impact Studies',
    description: 'Research on AI adoption and labor market effects.',
    sourceCount: 5,
    color: 'primary',
    updatedAt: '3d ago',
  },
];

export const tagTopics: TagTopic[] = [
  { id: 'TG-01', label: 'transformers', type: 'tag', count: 12 },
  { id: 'TG-02', label: 'Machine Learning', type: 'topic', count: 24 },
  { id: 'TG-03', label: 'RAG', type: 'tag', count: 8 },
  { id: 'TG-04', label: 'AI Safety', type: 'topic', count: 16 },
  { id: 'TG-05', label: 'inference', type: 'tag', count: 9 },
  { id: 'TG-06', label: 'Multimodal AI', type: 'topic', count: 7 },
  { id: 'TG-07', label: 'quantization', type: 'tag', count: 5 },
  { id: 'TG-08', label: 'AI Infrastructure', type: 'topic', count: 11 },
  { id: 'TG-09', label: 'alignment', type: 'tag', count: 6 },
  { id: 'TG-10', label: 'Edge AI', type: 'topic', count: 4 },
];

export const notifications: Notification[] = [
  {
    id: 'NTF-01',
    title: 'Source ready for review',
    description: 'Transformer Architecture: Attention Mechanisms Revisited completed processing.',
    type: 'info',
    time: '2h ago',
    read: false,
    link: '/review',
  },
  {
    id: 'NTF-02',
    title: 'Delivery failed',
    description: 'Aether Bridge delivery for Federated Learning Privacy Guarantees failed after 3 attempts.',
    type: 'error',
    time: '3h ago',
    read: false,
    link: '/delivery',
  },
  {
    id: 'NTF-03',
    title: 'Storage at 72%',
    description: 'Storage usage is approaching the warning threshold. Consider archiving old sources.',
    type: 'warning',
    time: '5h ago',
    read: false,
    link: '/usage',
  },
  {
    id: 'NTF-04',
    title: 'Source approved',
    description: 'Neuro-Symbolic Reasoning was approved and is ready for delivery.',
    type: 'success',
    time: '1d ago',
    read: true,
    link: '/approved',
  },
];

export const dashboardMetrics = {
  new: 3,
  processing: 2,
  needsReview: 2,
  approved: 4,
  failed: 1,
  delivered: 6,
};

export const usageData = {
  aiRequestsToday: 1842,
  aiRequestsLimit: 5000,
  monthlyUsage: [
    { day: 'W1', value: 12000 },
    { day: 'W2', value: 18500 },
    { day: 'W3', value: 14200 },
    { day: 'W4', value: 22100 },
  ],
  processingJobs: 6,
  failedJobs: 1,
  storageUsed: 72,
  storageLimit: 100,
  deliveryEvents: 48,
  deliveryTrend: '+12%',
  largeFiles: [
    { name: 'SRC-0479_full_text.pdf', size: '142 MB', age: '12m' },
    { name: 'SRC-0481_figures.tar.gz', size: '88 MB', age: '2h' },
    { name: 'SRC-0462_dataset.h5', size: '256 MB', age: '15d' },
  ],
};

export const serviceHealth = [
  { name: 'AI Processing', status: 'operational', latency: '240ms' },
  { name: 'Aether Bridge', status: 'degraded', latency: '1.2s' },
  { name: 'Storage', status: 'operational', latency: '45ms' },
  { name: 'Search Index', status: 'operational', latency: '120ms' },
];

export function getSourceById(id: string): Source | undefined {
  return sources.find((s) => s.id === id);
}

export function getSourcesByStatus(status: SourceStatus): Source[] {
  return sources.filter((s) => s.status === status);
}

export const reviewQueue = sources.filter(
  (s) => s.status === 'needs_review' || s.status === 'new'
);
